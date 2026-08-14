"""Schema tests for the shared T13/T21 founder demo dataset."""

from collections import Counter

from scripts.seed_demo_founder import DEMO_MEMORIES


def get_performance_posts():
    """Return published simulated LinkedIn episodic memories."""

    return [
        memory
        for memory in DEMO_MEMORIES
        if (
            memory["memory_type"] == "episodic"
            and memory["metadata"].get("channel") == "linkedin"
            and memory["metadata"].get("status") == "published"
        )
    ]


def test_demo_dataset_contains_meaningful_performance_sample():
    posts = get_performance_posts()

    assert len(posts) >= 4


def test_performance_posts_use_shared_analytics_schema():
    posts = get_performance_posts()

    content_ids = []

    for post in posts:
        metadata = post["metadata"]

        assert metadata["simulated"] is True

        for field_name in (
            "content_id",
            "title",
            "theme",
            "icp",
            "messaging_angle",
        ):
            assert isinstance(metadata[field_name], str)
            assert metadata[field_name].strip()

        engagement = metadata["engagement"]

        assert set(engagement) == {
            "likes",
            "comments",
            "clicks",
        }

        for metric in engagement.values():
            assert isinstance(metric, int)
            assert not isinstance(metric, bool)
            assert metric >= 0

        content_ids.append(metadata["content_id"])

    assert len(content_ids) == len(set(content_ids))


def test_dataset_supports_each_comparison_dimension():
    posts = get_performance_posts()

    themes = Counter(
        post["metadata"]["theme"]
        for post in posts
    )
    icps = Counter(
        post["metadata"]["icp"]
        for post in posts
    )
    messaging_angles = Counter(
        post["metadata"]["messaging_angle"]
        for post in posts
    )

    assert len(themes) >= 2
    assert len(icps) >= 2
    assert len(messaging_angles) >= 2

    assert all(count >= 2 for count in themes.values())
    assert all(count >= 2 for count in icps.values())
    assert all(
        count >= 2
        for count in messaging_angles.values()
    )