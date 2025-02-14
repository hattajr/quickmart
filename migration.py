from database import download_master_table


if __name__ == "__main__":
    print("Starting migrating...")
    download_master_table()
    print("Success migrate master database")