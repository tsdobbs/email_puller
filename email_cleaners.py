import re
import BeautifulSoup

#replaces html codes with the characters they represent, since it's safe it use the actual characters in plaintext
def htmlUnescape(m):
    try:
        return unichr(int(m.group(1), 10))
    except:
        return m.group()

#replaces all hyperlinks in emails with ' some website ', since it's not super meaningful for data analysis
#When we look for hyperlinks, we say URLs end with a space, and can extend over newlines (because they often do in emails)
#   This leads to sometimes accidentally grabbing the word right after the URL if there was only a newline.
#   The solution implemented is to add back any string at the end of a URL that comes after a newline and has no slashes (i.e. Looks like a word)
#   Sometimes you'll get the end of a URL added back in, but oh well
def replace_hyperlinks(m):
    try:
        return ' some website ' + m.group()[re.search('\n[^/]* ',m.group()).start():]
    except:
        return ' some_website '

# This part gets rid of any previous emails that were appended to the end of the email we're currently looking at
# It looks for a Regex along the lines of "On [some date], [someone] wrote:", as well as a number of other common email delimiters
def strip_replies(payload):
    match_list = list()
    match_list.append('<div[^>]*class=[^>]*"(gmail|yahoo)_(extra|quoted?)"[^>]*>')
    #This is the more specific version of the GMail reply line. Included here just incase there's a line break at the end of the line, which happens sometimes
    match_list.append('(?s)On( [A-Z][a-z]{2},)? [A-Z][a-z]{2} [0-9]{1,2}, [0-9]{4},? (at )?[0-9]{1,2}:[0-9]{2} [AP]M,.*wrote:')
    match_list.append('On .* wrote:')
    match_list.append('(?m)^-- ?$')
    match_list.append('(?i)-* *(Original|Forwarded) Message *-*')
    match_list.append('(?m)^_{32}')
    match_list.append('(?m)^From: ')
    match_list.append('(?m)^(<[^>]*>)?Sent from my.*')
    #This one is very aggressive - if a line starts with '>' we say that now it's a reply, but the philosophy here is that we'd rather lose some good data than allow any bad data in.
    match_list.append('(?m)^(<[^>]*>)?>')
    for match_string in match_list:
        if re.search(match_string, payload):
            reply_start = re.search(match_string, payload).start()
            payload = payload[:reply_start]
    return payload

#This part removes all the html tags, as well as a number of common html escape codes and long URLs
def strip_html(html_payload):
    html_payload = html_payload.replace('=\r\n','')  # line breaks need to be replaced first because they can be in the middle of the others
    html_payload = strip_replies(html_payload)
    html_payload = html_payload.replace('<br>','=C2=A0\r\n')
    html_payload = html_payload.replace('</div><div>', '=C2=A0\r\n')
    soup = BeautifulSoup.BeautifulSoup(html_payload)
    text_payload = soup.text
    text_payload = re.sub('&#([^;]+);', htmlUnescape, text_payload)
    text_payload = re.sub('(?ms)https?://[^ ]*( |$)', replace_hyperlinks, text_payload)

    replacement_dict = {'(=([A-Z]|[0-9]){2})+':' ', '&lt;':'<', '&gt;':'>', '&quot;':'"'}
    for key in replacement_dict:
        text_payload = re.sub(key, replacement_dict[key], text_payload)

    #Change the delimiter between emails by changing the string that's added to the end of the text here
    return text_payload + '\n\n'