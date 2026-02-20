import os
import csv


def get_version_numbers(version_path, doc_title):
    csv_filename = os.path.join(version_path, "{}.csv".format(doc_title))
    try:
        with open(csv_filename, newline="") as csvfile:
            reader = csv.reader(csvfile)
            # Skip the header row
            next(reader, None)
            version_numbers = [row[0] for row in reader]
            return version_numbers
    except FileNotFoundError:
        return []


def create_version_csv(csv_file_path, results, version_name):
    """
    Creates a CSV file containing version information.

    The function opens a CSV file with the name 'versions ' + str(doc_title) + '.csv'
    and writes the data from the provided row_list. The file is created or overwritten
    if it already exists.

    Parameters:
    - None

    Returns:
    - None
    """
    
    row_list = [["Version name", "Version ID"], [version_name, results["version_id"]]]

    with open(csv_file_path, "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(row_list)


def add_version(csv_file_path, results, version_name):
    #titre=get_doc_title()
    """

    Adds a new version entry to the CSV file.

    The function reads the existing CSV file to determine the current number of versions,
    increments the version counter, and appends a new row with the updated version information.
    The new row is also written to the CSV file.

    Global Variables:
    - row_list: A list containing rows of data for the CSV file.

    Parameters:
    - None

    Returns:
    - None
    """

    with open(csv_file_path, "a", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow([version_name, results["version_id"]])
