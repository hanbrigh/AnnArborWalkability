import json
import pandas as pd
from pathlib import Path

def extract_post_and_comments(raw_data):
    post = {}
    comments = []

    for listing in raw_data:
        if not isinstance(listing, dict) or "data" not in listing:
            continue
        children = listing["data"].get("children", [])

        # Extract post (kind = t3)
        if children and children[0]["kind"] == "t3":
            post_data = children[0]["data"]
            post = {
                "type": "post",
                "id": post_data.get("id"),
                "parent_id": None,
                "author": post_data.get("author"),
                "subreddit": post_data.get("subreddit"),
                "title": post_data.get("title"),
                "body": post_data.get("selftext", "").strip(),
                "score": post_data.get("score"),
                "num_comments": post_data.get("num_comments"),
                "created_utc": post_data.get("created_utc"),
                "url": post_data.get("url"),
            }

        # Extract comments (kind = t1)
        elif children and children[0]["kind"] == "t1":
            def parse_comment(comment):
                data = comment.get("data", {})
                comment_obj = {
                    "type": "comment",
                    "id": data.get("id"),
                    "parent_id": data.get("parent_id"),
                    "author": data.get("author"),
                    "subreddit": data.get("subreddit"),
                    "title": None,
                    "body": data.get("body", "").strip(),
                    "score": data.get("score"),
                    "num_comments": None,
                    "created_utc": data.get("created_utc"),
                    "url": f"https://reddit.com{data.get('permalink')}"
                    if data.get("permalink") else None,
                }
                # Recursively handle replies
                replies = data.get("replies")
                if isinstance(replies, dict):
                    reply_children = replies.get("data", {}).get("children", [])
                    for r in reply_children:
                        if r.get("kind") == "t1":
                            comments.append(parse_comment(r))
                return comment_obj

            for c in children:
                if c.get("kind") == "t1":
                    comments.append(parse_comment(c))

    return post, comments


def process_folder(folder_path: str, output_file: str = "reddit_combined.csv"):
    """Processes all .json files in a folder and combines them into one DataFrame."""
    folder = Path(folder_path)
    all_records = []

    json_files = list(folder.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {folder}")
        return

    print(f"Found {len(json_files)} JSON files in {folder}...")

    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            post, comments = extract_post_and_comments(raw_data)

            # Tag file source for traceability
            for item in [post] + comments:
                item["source_file"] = file.name

            all_records.extend([post] + comments)
            print(f"Processed {file.name} ({len(comments)} comments)")
        except Exception as e:
            print(f"Error processing {file.name}: {e}")

    df = pd.DataFrame(all_records)

    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"\nCombined data saved to {output_file}")
    print(df.head())

    return df


if __name__ == "__main__":
    df = process_folder("reddit_jsons", output_file="reddit_combined.csv")
