import imaplib
from email.parser import Parser
import email_cleaners

#pulls apart the payload object to get the actual email text, then cleans that text so it can be written to a textfile
def payload_parser(payload):
    try:
        parsed_payload = ''
        #Sometimes the payload object is a list of payload parts, e.g. [plaintext, htmltext, maybe an atttachment]
        #This for-loop iterates over the payload object until it finds something that returns a string of text, which we assume is probably the text we're looking for
        #The loop is happy with the first text it gets back. It might make more sense to prefer the plaintext part or the html part - something to consider changing.
        if type(payload._payload) is list:
            for part in payload._payload:
                parsed_payload = payload_parser(part)
                if parsed_payload != '': break
        else:
            #Pull the payload text and send it to functions that strip out replies and html junk
            #Currently, we don't differentiate between how to process plaintext or html, because sometimes things labeled as plaintext still have html codes in them for some reason (email is frustrating and poorly standardized, you see)
            #There might be some optimization to be done in having the two types of content treated differently
            if 'text/plain' in (payload['content-type'] or payload._default_type):
                parsed_payload += [email_cleaners.strip_html(payload._payload)]
            elif 'text/html' in payload['content-type']:
                parsed_payload += [email_cleaners.strip_html(payload._payload)]
        return parsed_payload
    except:
        return ''

voice = raw_input('Target Email Address:')
#config.txt should be a 2-line file containing the user login, followed by the user password
#   note that gmail wants bots (like this one!) to use a special application-specific password that's generated for only this app
login_details = open('config.txt','r')
login = login_details.readline()
password = login_details.readline()

#IMAP Login Stuff. Change tihs stuff if using a different mail service
M = imaplib.IMAP4_SSL('imap.gmail.com')
M.login(login, password)
#Select the mailbox. "[Gmail]/All Mail" gives all mail on the server, but there are other options for Gmail one can look up
M.select('"[Gmail]/All Mail"', readonly = True)
#Pull all emails from the target address from the user's All Mail mailbox
typ, data = M.search(None, '(FROM "%s")' % (voice))

#open textfile in the local folder
textfile = open('All Emails From ' + voice +'.txt','w')

for num in data[0].split():
    #Grab the content from each email pulled - RFC822 is an email standard that includes content info, among other things
    typ, data = M.fetch(num, '(RFC822)')

    #Parser turns the nonsense we got from the above fetch command into an object with a .payload attribute, so we can just get the actual content
    parsed_email = Parser().parsestr(data[0][1])
    #We send the parsed email on to the payload parser, where we get the actual content and clean it up before sending it to be written to a textfile
    parsed_payload = payload_parser(parsed_email)

    try:
        textfile.write(parsed_payload[0])
    except:
        pass

M.close()
M.logout()
textfile.close()