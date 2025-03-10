from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

@extend_schema(
    summary="Retrieve all posts",
    description="Fetches all public and friends-only posts visible to the authenticated user.",
    responses={
        200: {
            "example": [
                {
                    "id": 1,
                    "title": "Post Title",
                    "content": "Post content",
                    "visibility": "PUBLIC",
                    "author": {
                        "id": "http://example.com/authors/1234",
                        "display_name": "Test Author"
                    },
                    "published": "2025-03-10T05:00:00Z"
                }
            ]
        }
    },
)
@api_view(["GET"])
def api_documentation(request):
    """Returns API documentation overview."""
    return Response({"message": "API documentation"})
