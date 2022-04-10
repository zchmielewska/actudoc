from django.core.files.storage import Storage
from django.utils import timezone

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


def save_history(data1, data2, user):
    """
    Saves history of the changes for documents attributes.

    Checks the following attributes: product, category, validity_start.

    :param data1: data dictionary for old document
    :param data2: data dictionary for new document
    :param user: user who performs changes
    :return: None
    """
    now = timezone.now()

    if not data1["product_id"] == data2["product_id"]:
        models.History.objects.create(
            document_id=data1["id"],
            element="product",
            changed_from=models.Product.objects.get(id=data1["product_id"]),
            changed_to=models.Product.objects.get(id=data2["product_id"]),
            changed_by=user,
            changed_at=now,
        )

    if not data1["category_id"] == data2["category_id"]:
        models.History.objects.create(
            document_id=data1["id"],
            element="document category",
            changed_from=models.Category.objects.get(id=data1["category_id"]),
            changed_to=models.Category.objects.get(id=data2["category_id"]),
            changed_by=user,
            changed_at=now,
        )

    if not data1["validity_start"] == data2["validity_start"]:
        models.History.objects.create(
            document_id=data1["id"],
            element="valid from",
            changed_from=data1["validity_start"],
            changed_to=data2["validity_start"],
            changed_by=user,
            changed_at=now,
        )

    if not data1["title"] == data2["title"]:
        models.History.objects.create(
            document_id=data1["id"],
            element="title",
            changed_from=data1["title"],
            changed_to=data2["title"],
            changed_by=user,
            changed_at=now,
        )

    if data1["description"] and data2["description"]:
        if not data1["description"] == data2["description"]:
            models.History.objects.create(
                document_id=data1["id"],
                element="description",
                changed_from=data1["description"],
                changed_to=data2["description"],
                changed_by=user,
                changed_at=now,
            )

    return None


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
