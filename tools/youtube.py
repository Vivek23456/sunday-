from playwright.sync_api import sync_playwright


CDP_URL = "http://127.0.0.1:9222"


def _connect():
    playwright = sync_playwright().start()

    try:
        browser = playwright.chromium.connect_over_cdp(
            CDP_URL
        )
    except Exception:
        playwright.stop()
        return None, None, None

    pages = []

    for context in browser.contexts:
        pages.extend(context.pages)

    youtube_pages = [
        page
        for page in pages
        if "youtube.com" in page.url
    ]

    if not youtube_pages:
        browser.close()
        playwright.stop()
        return None, None, None

    watch_pages = [
        page
        for page in youtube_pages
        if "/watch" in page.url
    ]

    page = (
        watch_pages[0]
        if watch_pages
        else youtube_pages[0]
    )

    return playwright, browser, page


def _close(playwright, browser):
    try:
        browser.close()
    except Exception:
        pass

    try:
        playwright.stop()
    except Exception:
        pass


def _main_video(page):
    return page.locator(
        "#movie_player video"
    ).first


def play_music() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "I couldn't find a YouTube tab in Brave."
        )

    try:
        video = _main_video(page)

        video.wait_for(
            state="attached",
            timeout=5000,
        )

        page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                if (!video) {
                    throw new Error(
                        "Main YouTube player not found."
                    );
                }

                if (video.paused) {
                    video.play();
                }
            }
            """
        )

        return "Playing music."

    except Exception as exc:
        return (
            f"I couldn't play the music: {exc}"
        )

    finally:
        _close(playwright, browser)


def pause_music() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "I couldn't find a YouTube tab in Brave."
        )

    try:
        video = _main_video(page)

        video.wait_for(
            state="attached",
            timeout=5000,
        )

        page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                if (!video) {
                    throw new Error(
                        "Main YouTube player not found."
                    );
                }

                if (!video.paused) {
                    video.pause();
                }
            }
            """
        )

        return "Paused the music."

    except Exception as exc:
        return (
            f"I couldn't pause the music: {exc}"
        )

    finally:
        _close(playwright, browser)


def resume_music() -> str:
    return play_music()


def next_track() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "I couldn't find a YouTube tab in Brave."
        )

    try:
        button = page.locator(
            "#movie_player .ytp-next-button"
        ).first

        if button.count() == 0:
            return (
                "I couldn't find the YouTube next button."
            )

        button.click(timeout=5000)

        return "Playing the next song."

    except Exception as exc:
        return (
            f"I couldn't play the next song: {exc}"
        )

    finally:
        _close(playwright, browser)


def previous_track() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "I couldn't find a YouTube tab in Brave."
        )

    try:
        button = page.locator(
            "#movie_player .ytp-prev-button"
        ).first

        if button.count() == 0:
            return (
                "I couldn't find the YouTube previous button."
            )

        button.click(timeout=5000)

        return "Playing the previous song."

    except Exception as exc:
        return (
            f"I couldn't play the previous song: {exc}"
        )

    finally:
        _close(playwright, browser)


def stop_music() -> str:
    return pause_music()


def start_radio() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "I couldn't find a YouTube tab in Brave."
        )

    try:
        page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                if (!video) {
                    throw new Error(
                        "Main YouTube player not found."
                    );
                }

                if (video.paused) {
                    video.play();
                }
            }
            """
        )

        return "YouTube recommendations are playing."

    except Exception as exc:
        return (
            f"I couldn't start the music: {exc}"
        )

    finally:
        _close(playwright, browser)


def music_status() -> str:
    playwright, browser, page = _connect()

    if page is None:
        return (
            "No YouTube tab is open in Brave."
        )

    try:
        title = page.title()

        state = page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                if (!video) {
                    return "unknown";
                }

                if (video.ended) {
                    return "ended";
                }

                return video.paused
                    ? "paused"
                    : "playing";
            }
            """
        )

        current_time = page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                return video
                    ? video.currentTime
                    : 0;
            }
            """
        )

        duration = page.evaluate(
            """
            () => {
                const video =
                    document.querySelector(
                        "#movie_player video"
                    );

                return video
                    ? video.duration
                    : 0;
            }
            """
        )

        return (
            f"YouTube is {state}. "
            f"Current video: {title}. "
            f"Position: "
            f"{current_time:.1f}s / "
            f"{duration:.1f}s."
        )

    except Exception as exc:
        return (
            f"I couldn't read YouTube status: {exc}"
        )

    finally:
        _close(playwright, browser)
