from django.core.files.storage import Storage

from document import models


def search(phrase, company):
    """
    Search documents with phrase.

    Finds all documents for the given comapny that contain the phrase in one or more of the following attributes:
    company document id, product, category, validity start, file, created by, created at.

    :param phrase: string, phrase based on which the documents are filtered
    :param company: company model object
    :return: queryset
    """

    company_documents = models.Document.objects.filter(company=company)
    d1 = company_documents.filter(company_document_id__icontains=phrase)
    d2 = company_documents.filter(product__name__icontains=phrase)
    d3 = company_documents.filter(product__model__icontains=phrase)
    d4 = company_documents.filter(category__name__icontains=phrase)
    d5 = company_documents.filter(validity_start__icontains=phrase)
    d6 = company_documents.filter(file__icontains=phrase)
    d7 = company_documents.filter(created_by__first_name__icontains=phrase)
    d8 = company_documents.filter(created_by__last_name__icontains=phrase)

    phrase_without_hash = phrase.replace("#", "")
    if isinstance(phrase_without_hash, int):
        d9 = company_documents.filter(company_document_id=phrase_without_hash)
    else:
        d9 = company_documents.filter(company_document_id__icontains=phrase_without_hash)

    d10 = company_documents.filter(title__icontains=phrase)
    d11 = company_documents.filter(description__icontains=phrase)

    all_documents = d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | d11
    documents = all_documents.distinct().order_by("-id")
    return documents


def get_filename_msg(saved_filename, sent_filename, company_name):
    """
    Get informational message about the changes to the filename.

    :param saved_filename: string, filename save on the disk
    :param sent_filename: string, filename sent in the form
    :param company_name: string, short name of the company
    :return: string, message
    """
    text = f"The file has been saved as {saved_filename}."

    valid_sent_filename = Storage().get_valid_name(sent_filename)
    sent_filepath = company_name + "/" + valid_sent_filename
    if models.Document.objects.filter(file=sent_filepath).exists():
        document = models.Document.objects.get(file=sent_filepath)
        text += f" File with the name {valid_sent_filename} is already associated with " \
                f"the document #{document.company_document_id}."

    return text


def user_is_contributor_or_admin(request):
    user_is_contributor = request.user.profile.role == "contributor"
    user_is_admin = request.user.profile.role == "admin"
    return user_is_contributor or user_is_admin


def user_is_employee(request, company_name):
    return request.user.profile.company.name == company_name
