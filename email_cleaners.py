import re
import BeautifulSoup


def htmlUnescape(m):
    """ Replaces HTML codes with the characters they represent, since it's safe it use the actual characters in plaintext """
    try:
        return unichr(int(m.group(1), 10))
    except:
        return m.group()


def replace_hyperlinks(m):
    """
    Replaces all hyperlinks in emails with ' some website ', since it's not super meaningful for data analysis
    When we look for hyperlinks, we say URLs end with a space, and can extend over newlines (because they often do in
     emails). This leads to sometimes accidentally grabbing the word right after the URL if there was only a newline.
     The solution implemented is to add back any string at the end of a URL that comes after a newline and has no
     slashes (i.e. Looks like a word). Sometimes you'll get the end of a URL added back in, but oh well
    :param m: a re.match() object where we found a hyperlink inside some text
    :return: either the string ' some_website ' or ' some_website ' followed by the very end of the re.match() object
    """
    try:
        return ' some website ' + m.group()[re.search('\n[^/]* ',m.group()).start():]
    except:
        return ' some_website '


def strip_replies(payload):
    """
    Gets rid of any previous emails that were appended to the end of the email we're currently looking at
     Creates a list of common indicators email services use to denote a reply has started, then checks for those
     in the email and deletes anything after them.
    :param payload: the content of the email in question, including replies and often HTML escapes and other junk
    :return payload: email content with (theoretically) all of the appended replies removed
    """
    match_list = list()
    # In HTML emails sometimes the replies live inside their own div, which is handy
    match_list.append('<div[^>]*class=[^>]*"(gmail|yahoo)_(extra|quoted?)"[^>]*>')
    match_list.append('On .* wrote:')
    # Below is the more specific version of the Gmail reply line.
    # Included here just incase there's a line break at the end of the line, which happens sometimes
    match_list.append('(?s)On( [A-Z][a-z]{2},)? [A-Z][a-z]{2} [0-9]{1,2}, [0-9]{4},? (at )?[0-9]{1,2}:[0-9]{2} [AP]M,.*wrote:')
    match_list.append('(?m)^-- ?$')
    match_list.append('(?i)-* *(Original|Forwarded) Message *-*')
    match_list.append('(?m)^_{32}')
    match_list.append('(?m)^From: ')
    match_list.append('(?m)^(<[^>]*>)?Sent from my.*')
    # Below is aggressive, but the philosophy here is that we'd rather lose some good data than allow any bad data in.
    match_list.append('(?m)^(<[^>]*>)?>')

    for match_string in match_list:
        if re.search(match_string, payload):
            reply_start = re.search(match_string, payload).start()
            payload = payload[:reply_start]
    return payload


def strip_html(html_payload):
    """
    Strips replies with strip_replies, then removes all the html tags, as well as a number of common html escape codes,
     long URLs, and other things that don't make for useful reading in a large dataset.
    :param html_payload: The content of an email, including all HTML and any appended replies
    :return text_payload: The content of an email with all HTML tags and appended replies stripped out
    """
    # Line breaks removed first because they can be in the middle of the other escapes or codes, disrupting the search
    html_payload = html_payload.replace('=\r\n','')

    html_payload = strip_replies(html_payload)

    html_payload = html_payload.replace('<br>','=C2=A0\r\n') # Preserve HTML line breaks in plaintext version
    html_payload = html_payload.replace('</div><div>', '=C2=A0\r\n')

    soup = BeautifulSoup.BeautifulSoup(html_payload)
    text_payload = soup.text # Remove all HTML tags

    text_payload = re.sub('&#([^;]+);', htmlUnescape, text_payload)
    text_payload = re.sub('(?ms)https?://[^ ]*( |$)', replace_hyperlinks, text_payload)

    # We iterate over a dictionary of HTML escapes to replace and what to replace them with. Can be added to!
    # Included in the dict is dropping any time we see >100 characters without a space. It's unlikely that's a word.
    replacement_dict = {'(=([A-Z]|[0-9]){2})+':' ', '&lt;':'<', '&gt;':'>', '&quot;':'"', '(?s)[^ ]{100,}':''}
    for key in replacement_dict:
        text_payload = re.sub(key, replacement_dict[key], text_payload)

    #Change the delimiter between emails by changing the string that's added to the end of the text here
    return text_payload + '\n\n'