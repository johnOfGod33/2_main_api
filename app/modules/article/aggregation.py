"""Reusable MongoDB stages for embedding article card fields (single $lookup)."""

ARTICLES_COLLECTION = "articles"


def lookup_article_listing_preview(
    local_article_id_field: str = "article_id",
) -> list[dict]:
    """
    Append after $match on offers/orders. Joins `articles` by string id and projects
    only fields needed for mobile list/detail headers.
    """
    return [
        {
            "$lookup": {
                "from": ARTICLES_COLLECTION,
                "let": {"aid": f"${local_article_id_field}"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$eq": [{"$toString": "$_id"}, "$$aid"]},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "id": {"$toString": "$_id"},
                            "title": 1,
                            "list_price": "$price",
                            "status": 1,
                            "primary_image_url": {"$arrayElemAt": ["$images", 0]},
                            "description_preview": {
                                "$let": {
                                    "vars": {
                                        "d": {"$ifNull": ["$description", ""]},
                                    },
                                    "in": {
                                        "$cond": [
                                            {"$gt": [{"$strLenCP": "$$d"}, 140]},
                                            {
                                                "$concat": [
                                                    {"$substrCP": ["$$d", 0, 140]},
                                                    "…",
                                                ]
                                            },
                                            "$$d",
                                        ]
                                    },
                                }
                            },
                        }
                    },
                ],
                "as": "_article_embed",
            }
        },
        {"$addFields": {"article": {"$first": "$_article_embed"}}},
        {"$project": {"_article_embed": 0}},
    ]
