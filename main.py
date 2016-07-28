import imaplib
from email.parser import Parser
import email_cleaners

def payload_parser(payload):
    """
    Pulls apart the payload object to get the actual email text, then cleans that text so it can be written to a textfile
    :param payload:
    :return parsed_payload:
    """
    try:
        parsed_payload = ''
        """
        Sometimes the payload object is a list of payload parts, e.g. [plaintext, htmltext, maybe an atttachment]
        This for-loop iterates over the payload object until it finds something that returns a string of text, which we assume is probably the text we're looking for
        The loop is happy with the first text it gets back. It might make more sense to prefer the plaintext part or the html part - something to consider changing.
        """
        if type(payload._payload) is list:
            for part in payload._payload:
                parsed_payload = payload_parser(part)
                if parsed_payload != '': break
        else:
            """
            Pull the payload text and send it to functions that strip out replies and html junk
            Currently, we don't differentiate between how to process plaintext or html, because sometimes things labeled as plaintext still have html codes in them for some reason (email is frustrating and poorly standardized, you see)
            There might be some optimization to be done in having the two types of content treated differently
            """
            if 'text/plain' in (payload['content-type'] or (not payload['content-type'] and 'text/plain' in payload._default_type)):
                parsed_payload = email_cleaners.strip_html(payload._payload)
            elif 'text/html' in payload['content-type']:
                parsed_payload = email_cleaners.strip_html(payload._payload)
        return parsed_payload
    except:
        return ''


def collect_imap_details():
    """
    Gets specifics for logging in and what emails we're interested in, then opens an IMAP connection and returns the
    IMAP object.
    config.txt should be a 2-line file containing the user login, followed by the user password. Note that gmail wants
    bots (like this one!) to use a special application-specific password that's generated for only for this app.
    :return M: IMAP object for interacting with IMAP server
    :return voice: Defines which emails we'll pull. Emails we're pulling were sent from this address
    """
    voice = raw_input('Target Email Address:')

    login_details = open('config.txt','r')
    login = login_details.readline()
    password = login_details.readline()

    #IMAP Login Stuff. Change this stuff if using a different mail service
    M = imaplib.IMAP4_SSL('imap.gmail.com')
    M.login(login, password)

    return M, voice


def get_emails(M, voice):
    """
    Selects the mailbox, then pulls all emails from the target address from that mailbox.
    The IMAP object and the pulled data are both returned.
    The "[Gmail]/All Mail" mailbox gives all mail on the server, but there are other options for Gmail one can look up.
    :param M: IMAP object for interacting with IMAP server
    :param voice: Emails we're pulling were sent from this address
    :return M: IMAP object for interacting with IMAP server, now in a 'selected' state
    :return data: Data from IMAP server describing which emails were sent from voice
    """
    M.select('"[Gmail]/All Mail"', readonly = True)
    typ, data = M.search(None, '(FROM "%s")' % (voice))
    return M, data


def parse_and_write_emails(M, data, voice):
    """
    Opens a textfile, parses the content from each email in 'data', writes that content to textfile, then closes it.
    :param M: IMAP object for interacting with IMAP server
    :param data: Data from IMAP server describing which emails were sent from voice
    :param voice: Emails we're pulling were sent from this address
    :return: None
    """

    textfile = open('All Emails From ' + voice +'.txt','w')

    for num in data[0].split():
        #RFC822 is an email standard that includes content info, among other things
        typ, data = M.fetch(num, '(RFC822)')
        #Parser turns the nonsense we got from the above fetch command into an object with a .payload attribute,
        #  so we can just get the actual content
        parsed_email = Parser().parsestr(data[0][1])
        #We send the parsed email on to the payload parser,
        # where we get the actual content and clean it up before sending it to be written to a textfile
        parsed_payload = payload_parser(parsed_email)

        try:
            textfile.write(parsed_payload)
        except:
            pass

    textfile.close()
    return

M, voice = collect_imap_details()
M, data = get_emails(M, voice)
parse_and_write_emails(M, data, voice)

M.close()
M.logout()