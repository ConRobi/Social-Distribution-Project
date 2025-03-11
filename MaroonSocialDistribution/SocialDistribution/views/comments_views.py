@api_view(['POST'])
@login_required
def add_comment(request, post_id):
    '''
    Add a comment to a post
    '''
    post = get_object_or_404(Post, id=post_id)
    comment_text = request.POST.get('comment')
    content_type = request.POST.get('contentType')
    comment = Comment.objects.create(author=request.user, post=post, comment=comment_text, contentType=content_type)
    comment.id = f"{request.user.id}/commented/{comment.uuid}"
    comment.save()
    return redirect("SocialDistribution:view-single-post", post_id=post_id)

@api_view(['GET'])
def get_post_comments(request, author_uuid, post_id):
    """
    - Description: Get a list of comments for a specified post
    - Returns: a paginated list of comments for a specific post
    """
    post = get_object_or_404(Post, id=post_id, author__uuid=author_uuid)
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    comments = Comment.objects.filter(post=post).order_by('-published')
    comment_count = comments.count()
    paginated_comments = paginator.paginate_queryset(comments, request)
    serialized_comments = CommentSerializer(paginated_comments, many=True).data

    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "comments",
        "page": f"{node_url}/authors/{author_uuid}/posts/{post_id}",
        "id": f"{node_url}/api/authors/{author_uuid}/posts/{post_id}/comments",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": comment_count,
        "src": [comment for comment in serialized_comments],
    })

@api_view(['GET'])
def get_comments_by_author(request, author_uuid):
    """
    Description: Get the list of comments by an author
    Returns: a paginated list of comment objects for a specific author
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    comments = Comment.objects.filter(author=author).order_by('-published')
    paginated_comments = paginator.paginate_queryset(comments, request)
    serialized_comments = CommentSerializer(paginated_comments, many=True).data
    comment_count = comments.count()

    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "comments",
        # TODO: page and id might be different because all these comments might not be on the same post
        # "page": f"{node_url}/authors/{author_uuid}/posts/{post_id}",
        # "id": f"{node_url}/api/authors/{author_uuid}/posts/{post_id}/comments",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": comment_count,
        "src": [comment for comment in serialized_comments],
    })

@api_view(['GET'])
def get_single_comment(request, author_uuid, comment_uuid):
    """
    Description: Get a single comment by an author
    Returns: a single comment by a specific author, identified by comment_uuid
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    comment = get_object_or_404(Comment, uuid=comment_uuid, author=author)
    serialized_comment = CommentSerializer(comment).data
    return Response(serialized_comment)