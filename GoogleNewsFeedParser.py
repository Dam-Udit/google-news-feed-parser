import datetime
import feedparser
import firebase_admin
from firebase_admin import credentials, firestore


class GoogleNewsFeedParser:
    def __init__(self, limit=None):
        self.limit = limit
        self.data = []

    def parse_google_news_feed(self, query):
        url = f'https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en'
        try:
            feed = feedparser.parse(url)

            if self.limit:
                entries = feed.entries[:self.limit]
            else:
                entries = feed.entries

            if feed.entries:
                for entry in entries:
                    title = entry.title
                    link = entry.link
                    description = entry.description
                    source = entry.source.title
                    published = entry.published

                    self.data.append(
                        {'url': url, 'title': title, 'link': link, 'description': description, 'source': source, 'published': published})
            else:
                print("Nothing Found!")
        except Exception as e:
            print(f"Error parsing the feed: {e}")

    def save_to_firestore(self, category, news_items):
        db = firestore.client()
        collection_ref = db.collection(category)
        outlet_count_ref = db.collection('outlet_counts').document(category)

        outlet_counts = {}

        for item in news_items:
            if isinstance(item, dict):
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
                shortened_title = item['title'][:30].replace(" ", "_")
                doc_id = f"{shortened_title}_{timestamp}"

                collection_ref.document(doc_id).set(item)

                source = item.get('source')
                if source:
                    outlet_counts[source] = outlet_counts.get(source, 0) + 1
            else:
                print(f"Unexpected item type: {type(item)} - {item}")

        outlet_count_ref.set(outlet_counts, merge=True)


if __name__ == "__main__":
    # Initialize the Firebase SDK
    cred = credentials.Certificate(
        "news-archiver-5f402-firebase-adminsdk-adkpd-36cf1da1a7.json")
    firebase_admin.initialize_app(cred)
    parser = GoogleNewsFeedParser(25)
    categories = ['Business', 'Technology', 'Sports', 'Markets',
                  'Politics', 'Entertainment', 'India', 'World']
    for category in categories:
        parser.parse_google_news_feed(category)
        parser.save_to_firestore(category, news_items=parser.data)
