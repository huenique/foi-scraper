"""
foi_scraper.utils
-----------------
"""


def save_page_url(url: str):
    """Record the URL of the page visted."""
    with open("pages.txt", mode="a+", encoding="utf-8") as file_object:
        file_object.write(f"{url}\n")


def count_requests(request_num: int):
    """Save number of recently extracted data."""
    with open("total_requests.txt", mode="r+", encoding="utf-8") as file_object:
        # Assuming the initial content of the file is 0
        num = int(file_object.read()) + request_num
        file_object.seek(0)
        file_object.write(str(num))
        file_object.truncate()


def total_requests() -> str:
    """Count the total number of requests collected."""
    with open("total_requests.txt", mode="r", encoding="utf-8") as file_object:
        return file_object.read()


if __name__ == "__main__":
    pass
