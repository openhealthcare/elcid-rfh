"""
Views for the letters Opal Plugin
"""
import os
import tempfile
from django.http.response import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.conf import settings
from django.views.generic import TemplateView, View
from django.http import HttpResponseServerError
from opal.core.views import json_response
from opal.core import application
from weasyprint import HTML, CSS
from django.template.loader import render_to_string


class LettersIndexView(LoginRequiredMixin, TemplateView):
    template_name = "letters/index.html"


def get_opal_css():
    """
    Returns all the css used in the base template.
    """
    stylesheets = [
        "bootstrap-3.1.0/css/bootstrap.css",
        "css/opal.css"
    ]
    stylesheets.extend(
        application.get_app().get_styles()
    )
    stylesheets.append("css/pdf.css")
    return stylesheets


def get_pdf_css(stylesheets):
    """
    Takes in the css paths relative from STATIC_URL
    Returns the css for used for creating pdfs.
    """
    css_paths = []
    for stylesheet in stylesheets:
        css_path = finders.find(stylesheet)
        if isinstance(css_path, (list, tuple)):
            css_paths.extend(css_path)
        else:
            css_paths.append(css_path)
    return [
        CSS(filename=os.path.realpath(path)) for path in css_paths
    ]


def path_to_file_name(path, suffix):
    """
    Converts a url path into a pdf file name
    e.g. "/my_letter/is.great", "pdf"
    becomes brand_name_my_letter_is_great.pdf
    """
    pdf_prefix = path.replace(
        ".", "_"
    ).replace(
        "/", "_"
    ).strip("_")
    return "{}{}.{}".format(settings.OPAL_BRAND_NAME, pdf_prefix, suffix)


def create_file_response(full_path, file_name):
    """
    Returns an http response that delivers a file
    """
    with open(full_path, 'rb') as download:
        content = download.read()

    resp = HttpResponse(content)
    disp = 'attachment; filename="{}"'.format(file_name)
    resp['Content-Disposition'] = disp
    return resp


def write_page_to_pdf_file(pdf_name, rendered_html, css_paths):
    tmp_dir = tempfile.mkdtemp()
    full_path = os.path.join(tmp_dir, pdf_name)
    css = get_pdf_css(css_paths)
    html = HTML(string=rendered_html)
    html.write_pdf(full_path, stylesheets=css)
    return full_path


class PdfMixin(object):
    """
    A mixin for a classed based template/detail/list view.
    if PDF_ASYNC is True, it returns the celery task rendering the view
    otherwise it returns the view as a pdf.
    """
    def get_pdf_name(self):
        pdf_name = getattr(self, "pdf_name", None)
        if pdf_name is None:
            pdf_name = path_to_file_name(self.request.path, "pdf")
        return pdf_name

    def get_css_paths(self):
        return get_opal_css()

    def render_view_to_string(self, context_data):
        return render_to_string(
            self.get_template_names(),
            context=context_data,
            request=self.request
        )

    def render_to_response(self, context_data, **response_kwargs):
        pdf_name = self.get_pdf_name()
        as_string = self.render_view_to_string(context_data)
        css_paths = self.get_css_paths()

        if settings.PDF_ASYNC:
            from plugins.letters import tasks
            as_string = self.render_view_to_string(context_data)
            task_id = tasks.create_pdf.delay(
                pdf_name, as_string, css_paths
            ).id
            return json_response({"id": task_id})
        else:
            full_path = write_page_to_pdf_file(pdf_name, as_string, css_paths)
            return create_file_response(full_path, pdf_name)


class AsyncDownLoad(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        from celery.result import AsyncResult
        from opal.core import celery
        task_id = kwargs['task_id']
        result = AsyncResult(id=task_id, app=celery.app)
        if result.state != 'SUCCESS':
            raise ValueError('Unable to create PDF')
        full_path, pdf_name = result.get()
        return create_file_response(full_path, pdf_name)
