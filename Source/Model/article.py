"""!
********************************************************************************
@file   article.py
@brief  Manage article template data persistence.
********************************************************************************
"""

import os
import logging
import enum
from typing import Any

from Source.Model.data_handler import read_json_files, add_json, delete_data, fill_data, \
    get_file_name, set_general_json_data

ARTICLE_FOLDER = "articles"
ARTICLE_TYPE = "article"

log = logging.getLogger(__name__)

JSON_VERSION_ARTICLE = "01.00.00"


class EArticleFields(str, enum.Enum):
    """!
    @brief Article template field identifiers.
    """
    JSON_TYPE = "json_type"
    JSON_VERSION = "json_version"
    ID = "id"
    NAME = "name"  # Artikelname (BT-153)
    DESCRIPTION = "description"  # Artikelbeschreibung (BT-154)
    ARTICLE_ID = "articleId"  # Artikel-Nr. (BT-155)
    NET_UNIT_PRICE = "netUnitPrice"  # Netto-Einzelpreis (BT-146)
    QUANTITY_UNIT = "quantityUnit"  # Einheit (BT-130)
    VAT_RATE = "vatRate"  # Steuersatz (BT-152)
    VAT_CODE = "vatCode"  # Steuerkategorie (BT-151)
    DEPOSIT = "deposit"  # Pfand pro Einheit
    CONTAINER_TYPE = "containerType"  # Kasten / Flasche / ""


ARTICLE_TEMPLATE: dict[EArticleFields, Any] = {
    EArticleFields.JSON_TYPE: "",
    EArticleFields.JSON_VERSION: "",
    EArticleFields.ID: "",
    EArticleFields.NAME: "",
    EArticleFields.DESCRIPTION: "",
    EArticleFields.ARTICLE_ID: "",
    EArticleFields.NET_UNIT_PRICE: 0.0,
    EArticleFields.QUANTITY_UNIT: "H87",
    EArticleFields.VAT_RATE: 0.0,
    EArticleFields.VAT_CODE: "S",
    EArticleFields.DEPOSIT: 0.0,
    EArticleFields.CONTAINER_TYPE: "",
}


def read_articles(path: str) -> list[dict[EArticleFields, Any]]:
    """!
    @brief Read all article template records.
    @param path : data directory path.
    @return List of article data dictionaries.
    """
    return read_json_files(os.path.join(path, ARTICLE_FOLDER), ARTICLE_TEMPLATE)


def add_article(path: str, add: bool, article: dict[EArticleFields, Any],
                article_id: str | None = None, rename: bool = False) -> None:
    """!
    @brief Add or update article template data.
    @param path : data directory path.
    @param add : whether to git-add the exported file.
    @param article : article data to export.
    @param article_id : unique article identifier.
    @param rename : whether to rename the file based on article data.
    """
    uid = set_general_json_data(article, ARTICLE_TYPE, EArticleFields.JSON_TYPE,
                                EArticleFields.JSON_VERSION, JSON_VERSION_ARTICLE,
                                EArticleFields.ID, article_id)
    instance = fill_data(ARTICLE_TEMPLATE, article)
    title = get_file_name(instance[EArticleFields.NAME], uid)
    id_field = EArticleFields.ID if (article_id is not None) else None
    add_json(add, instance, title, uid, os.path.join(path, ARTICLE_FOLDER), id_field=id_field, rename=rename)


def remove_article(path: str, article_id: str) -> None:
    """!
    @brief Remove article template data.
    @param path : data directory path.
    @param article_id : unique article identifier to delete.
    """
    delete_data(os.path.join(path, ARTICLE_FOLDER), article_id, id_field=EArticleFields.ID)
