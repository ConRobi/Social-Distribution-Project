import pytest
from rest_framework.test import APIClient
from SocialDistribution.models import Post, Author  # ✅ Use Author instead of User
import uuid

@pytest.fixture
def client(db):
    """Create an API client and authenticate a Django user."""
    client = APIClient()

    # ✅ Create an Author instead of a User
    test_user = Author.objects.create_user(
        username="testuser", 
        password="testpassword",
        display_name="Test User",
        id="http://example.com/authors/" + str(uuid.uuid4()),
        uuid=uuid.uuid4(),
        host="http://example.com/",
        github="https://github.com/testuser",
        profile_image="",
        page="http://example.com/authors/testuser"
    )

    client.force_authenticate(user=test_user)  # ✅ Authenticate with Author model
    return client

@pytest.fixture
def test_author(db):
    """Create a test author before running post-related tests."""
    return Author.objects.create(
        username="testauthor",  # ✅ Required by AbstractUser
        password="testpassword",
        display_name="Test Author",
        id="http://example.com/authors/" + str(uuid.uuid4()),
        uuid=uuid.uuid4(),
        host="http://example.com/",
        github="https://github.com/testauthor",
        profile_image="",
        page="http://example.com/authors/testauthor"
    )

@pytest.fixture
def test_post(db, test_author):
    """Create a test post before running the test."""
    return Post.objects.create(
        id=1,
        title="Test Post",
        content="This is a test post",
        visibility="PUBLIC",
        author=test_author
    )

def test_read_post(client, test_post):
    """Test retrieving a public post."""
    response = client.get(f"/posts/{test_post.id}/")
    assert response.status_code == 200


def test_read_unlisted_post(client, db, test_author):
    """Test retrieving an unlisted post."""
    
    # ✅ Debug: Print all posts before creating one
    print("Posts before test:", list(Post.objects.values()))

    # ✅ Create the post
    unlisted_post = Post.objects.create(
        id=2,
        title="Unlisted Post",
        content="This is an unlisted post",
        visibility="UNLISTED",
        author=test_author
    )

    # ✅ Debug: Print all posts after creating one
    print("Posts after test:", list(Post.objects.values()))

    response = client.get(f"/posts/{unlisted_post.id}/")

    # ✅ Debug: Print response details
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.content}")

    assert response.status_code == 200, f"Unexpected status code: {response.status_code} - Response: {response.content}"


