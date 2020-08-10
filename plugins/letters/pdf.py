import os
import tempfile
from django.contrib.staticfiles import finders
from django.conf import settings
from opal.core import application
from opal.utils import camelcase_to_underscore
from weasyprint import HTML, CSS
from django.template.loader import render_to_string


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


def view_to_file_name(view_cls, some_object, suffix):
    """
    Converts a url path into a pdf file name
    e.g. "/my_letter/is.great", "pdf"
    becomes brand_name_my_letter_is_great.pdf
    """
    snake_case = camelcase_to_underscore(view_cls.__name__)
    brand_name = settings.OPAL_BRAND_NAME.replace(" ", "_").lower()
    return "{}_{}_{}.{}".format(
        brand_name, snake_case, some_object.id, suffix
    )

def write_page_to_pdf_file(pdf_name, rendered_html, css_paths):
    tmp_dir = tempfile.mkdtemp()
    full_path = os.path.join(tmp_dir, pdf_name)
    css = get_pdf_css(css_paths)
    html = HTML(string=rendered_html)
    html.write_pdf(full_path, stylesheets=css)
    return full_path


def render_detail_view_to_string(view_cls, some_object):
    view = view_cls()
    view.object = some_object
    context_data = view.get_context_data()
    return render_to_string(
        view.get_template_names(),
        context=context_data,
    )

def render_detail_view_to_pdf(view_cls, some_object):
    file_name = view_to_file_name(view_cls, some_object, "pdf")
    view_as_string = render_detail_view_to_string(view_cls, some_object)
    css = get_opal_css()
    return write_page_to_pdf_file(file_name, view_as_string, css)