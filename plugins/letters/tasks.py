from __future__ import absolute_import
from celery import shared_task


@shared_task
def create_pdf(pdf_name, as_string, css_paths):
    from plugins.letters.views import write_page_to_pdf_file
    full_path = write_page_to_pdf_file(pdf_name, as_string, css_paths)
    return full_path, pdf_name
