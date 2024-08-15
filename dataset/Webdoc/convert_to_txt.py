import argparse
import os
from resiliparse.extract.html2text import extract_plain_text
import bs4

# parses html and delets all text in text elements that are shorter than min_length
def keep_text_longer_than_from_html(html, min_length=100):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    # only keep elements in body
    
    for tag in soup.find_all():
        if len(tag.text) < min_length:
            tag.extract()
    
    return str(soup)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_folder", default="crawl/warc", help="The folder where files would be input")
    parser.add_argument("-o", "--output_folder", default="crawl/txt", help="The folder where files would be output")
    parser.add_argument("-m", "--min_length", default=50, help="The minimum length of text to keep")

    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    min_length = args.min_length

    if min_length > 0:
        output_folder += "_min_length_" + str(min_length)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # iterate over subfolders
    for subfolder in os.listdir(input_folder):
        print("converting", subfolder)
        subfolder_path = os.path.join(input_folder, subfolder)
        out_path = os.path.join(output_folder, subfolder)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        if os.path.isdir(subfolder_path):
            # iterate over files in subfolder
            for filename in os.listdir(subfolder_path):
                input_file = os.path.join(subfolder_path, filename)
                output_file = os.path.join(output_folder, subfolder, filename + ".txt")
                with open(input_file, "r") as f:
                    in_file = f.read()

                txt = keep_text_longer_than_from_html(in_file, min_length=min_length)
                txt = extract_plain_text(txt, main_content=False, preserve_formatting=False,  alt_texts=False)
                if len(txt) < min_length:
                    print("skipping", input_file)

                with open(output_file, "w") as f:
                    f.write(txt)

        else:
            print("skipping", subfolder)