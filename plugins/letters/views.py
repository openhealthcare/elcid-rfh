"""
Views for the letters Opal Plugin
"""
import os
import tempfile
from django.http.response import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.conf import settings
from django.views.generic import TemplateView
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


class PdfMixin(object):
    """
    A mixin for a classed based template/detail/list view.
    that returns returns the view as a pdf.
    """
    def get_pdf_name(self):
        pdf_name = getattr(self, "pdf_name", None)
        if pdf_name is None:
            pdf_name = path_to_file_name(self.request.path, "pdf")
        return pdf_name

    def get_css(self):
        opal_css = get_opal_css()
        return get_pdf_css(opal_css)

    def render_pdf(self, context_data, pdf_name):
        """
        Render the view into a file in the temp directory
        and return the path of the file.
        """
        tmp_dir = tempfile.mkdtemp()
        full_path = os.path.join(tmp_dir, pdf_name)
        css = self.get_css()
        html = HTML(string=render_to_string(
            self.get_template_names(),
            context=context_data,
            request=self.request
        ))
        html.write_pdf(full_path, stylesheets=css)
        return full_path

    def render_to_response(self, context_data, **response_kwargs):
        pdf_name = self.get_pdf_name()
        full_path = self.render_pdf(context_data, pdf_name)
        return create_file_response(full_path, pdf_name)
