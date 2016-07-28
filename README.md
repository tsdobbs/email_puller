# email_puller
*Abstract:* Pulls emails from an IMAP server and writes the plaintext content to a file

Originally written to pull all of the emails sent to my Gmail account from a particular person, then clean them so that data analysis can be done on the words. Could be easily tweaked to pull from any IMAP server or to pull emails with other characteristics (e.g. all sent emails, or emails written between two dates).  

## Requirements:  
- Python 2.7
- [A Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- imaplib and email libraries (included in Python 2.7)

## Setup:  
Using Gmail, just create a file called 'config.txt' in the same directory as the script with two lines:
  - Username of the account you're trying to log into
  - Password for that account  
  
A model file called _config.txt is included in this repo. Note that Gmail requires you to create a special application-specific password when trying to access it with a script.  

If you're using something besides Gmail, you'll have to tweek the IMAP settings inside main.py
