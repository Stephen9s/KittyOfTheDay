from bs4 import BeautifulSoup
import urllib.request
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import sys
import time

fromaddr = "EMAIL"
toaddr = "EMAIL"
tryagain = 60*60*4 # 4 hours
kotd_url = "http://dailykitten.com/"
output_ext = ".unk"
allowed_ext = ['.jpg', '.gif', '.png', '.jpeg']


def send_email(filename):
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Kitty of the Day!"
    msg.attach(MIMEText("Today's Kitty is... [this will be automated soon; written just for you, love!]", 'plain'))
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)

    with smtplib.SMTP(host='SERVER', port=587, timeout=10) as server:
        server.set_debuglevel(True)
        server.starttls()
        server.login(fromaddr, "PASSWORD")
        text = msg.as_string()

        try:
            server.sendmail(fromaddr, toaddr, text)
        except Exception as err:
            raise Exception("Problem with connecting to mail service.")
        finally:
            server.quit()


def validate_date(article):
    valid = False
    day = article.find_all("div", {'class': 'day'}, limit=1)[0].text
    month = article.find_all("div", {'class': 'month'}, limit=1)[0].text
    year = article.find_all("div", {'class': 'year'}, limit=1)[0].text

    if day and month and year:
        today = datetime.date.today()
        y, m, d = today.strftime("%Y-%B-%d").split('-')

        if y == year and d == day and m == month:
            valid = True

    return valid


def main():
    kitty_sent = False

    while not kitty_sent:
        try:
            page = None
            soup = None

            with urllib.request.urlopen(kotd_url) as f:
                page = f.read()

            # Beautify!
            soup = BeautifulSoup(page, "html.parser")
            articles = soup.find_all("article", limit=1)

            if len(articles):
                article = articles[0]
                kotd_img = article.find_all("img", {'class': 'attachment-featured'}, limit=1)

                if validate_date(article) and kotd_img:
                    if len(kotd_img):
                        src = kotd_img[0]['src']
                        f_img = urllib.request.urlopen(src)
                        output_ext = src[-4:]

                        if filter(lambda x: output_ext.lower in x, allowed_ext):
                            kitty = open("kitty%s" % output_ext, "wb")
                            kitty_data = f_img.read()
                            kitty.write(kitty_data)
                            f_img.close()

                        else:
                            raise Exception("Bad image extension found in img src.")

                        if len(kitty_data):
                            send_email("kitty%s" % output_ext)
                        else:
                            raise Exception("Kitty IMG has no data!")

                        kitty_sent = True

                    else:
                        raise Exception("No kitty found!")
                else:
                    print("Trying again...")
                    time.sleep(tryagain)

            else:
                raise Exception("No kitty found!")

        except Exception as err:
            print(err)
            sys.exit(1)


if __name__ == "__main__":
    main()
