import lxml.html
import re

_table_tr_re = re.compile(r"\</?tr/?\>", re.IGNORECASE)

def table_to_iter(table_string):
    """Takes a table on isis that is a list of items with fields designated by a
    single header, and converts them into a iterator of dicts, with keys based
    on the header, and values based on each row's cells. For example, we can
    take a table like the schedule table::
    
        section  type  course   credits  days   periods  building  room
        0234     X     NOM2222  4        M W F  2        KITE      C101
                                         W      3        BUG       007
        1230     X     DRA1234  3        M W F  1 2      DOG       G121
                                         R      1 2 3    MIL       G121
        9999     X     ABC9876  5        TBA    TBA      JACK      TBA
    
    and turn it into an iterator of dictionaries like::
    
        [
            {"section":"0234", "type":"X", "course":"NOM2222", "credits":"4",
             "days":"M W F", "periods":"2", "building":"KITE", "room":"C101"},
            {"section":None, "type":None, "course":None, "credits":None,
             "days":"W", "periods":"3", "building":"BUG", "room":"007"},
            {"section":"1230", "type":"X", "course":"DRA1234", "credits":"3",
             "days":"M W F", "periods":"1 2", "building":"DOG", "room":"G121"},
            {"section":None, "type":None, "course":None, "credits":None,
             "days":"R", "periods":"1 2 3", "building":"MIL", "room":"G121"},
            {"section":"9999", "type":"X", "course":"ABC9876", "credits":"5",
             "days":"TBA", "periods":"TBA", "building":"JACK", "room":"TBA"}
        ]
    
    The header is discarded."""
    rows = lxml.html.fragment_fromstring(
        "<table>%s</table>" % _fix_table_html(
            table_string
        )
    )
    headers = [i.text.strip().lower() for i in rows[0]]
    for r in rows[1:]:
        d = {}; i = 0; k = 0
        while i < len(r):
            tag = r[i]
            text = tag.text.strip() if tag.text else None
            if not text: text = None
            if "colspan" in tag.attrib:
                span = int(tag.get("colspan").strip())
                for m in range(span):
                    if k + m >= len(headers):
                        break # fucking broken isis html
                    d[headers[k + m]] = text
                k += span
            else:
                d[headers[k]] = text
                k += 1
            i += 1
        yield d

def table_to_list(table_string):
    """Does the same thing as :func:`table_to_iter`, but gives a list instead of
    an iterator."""
    return list(table_to_iter(table_string))

def _fix_table_html(source):
    """Fixes ISIS' poor tagging of table rows. Source should be a string with
    the contents of the table, excluding the <table> tags."""
    rows = [i for i in [k.strip() for k in _table_tr_re.split(source)] if i]
    return "<tr>%s</tr>" % "</tr><tr>".join(rows)
