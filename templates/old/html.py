# -*- coding: utf-8 -*-
"""Translate utf-8 codes to html codes"""

def encode(data):
   for utf, xml in utf_xml:
      data = data.replace(utf, xml)
   return data


def decode(data):
   data = unicode(data)
   for utf, xml in utf_xml:
      data = data.replace(xml, utf)
   return data


utf_xml = [
    #[u' ', '&nbsp;'  ],  [u'\n', '<br />' ]
    #[u'>', '&gt;'    ],  [u'<', '&lt;'    ],
    [u'¡', '&iexcl;' ],
    [u'¢', '&cent;'  ],  [u'£', '&pound;' ],
    [u'¤', '&curren;'],  [u'¥', '&yen;'   ],
    [u'¦', '&brvbar;'],  [u'§', '&sect;'  ],
    [u'¨', '&uml;'   ],  [u'©', '&copy;'  ],
    [u'ª', '&ordf;'  ],  [u'«', '&laquo;' ],
    [u'¬', '&not;'   ],  [u'®', '&reg;'   ],
    [u'¯', '&macr;'  ],  [u'°', '&deg;'   ],
    [u'±', '&plusmn;'],  [u'¹', '&sup1;'  ],
    [u'²', '&sup2;'  ],  [u'³', '&sup3;'  ],
    [u'´', '&acute;' ],  [u'µ', '&micro;' ],
    [u'¶', '&para;'  ],  [u'·', '&middot;'],
    [u'¸', '&cedil;' ],  [u'º', '&ordm;'  ],
    [u'»', '&raquo;' ],  [u'¼', '&frac14;'],
    [u'½', '&frac12;'],  [u'¾', '&frac34;'],
    [u'¿', '&iquest;'],  [u'À', '&Agrave;'],
    [u'Á', '&Aacute;'],  [u'Â', '&Acirc;' ],
    [u'Ã', '&Atilde;'],  [u'Ä', '&Auml;'  ],
    [u'Å', '&Aring;' ],  [u'Æ', '&AElig;' ],
    [u'Ç', '&Ccedil;'],  [u'È', '&Egrave;'],
    [u'É', '&Eacute;'],  [u'Ê', '&Ecirc;' ],
    [u'Ë', '&Euml;'  ],  [u'Ì', '&Igrave;'],
    [u'Í', '&Iacute;'],  [u'Î', '&Icirc;' ],
    [u'Ï', '&Iuml;'  ],  [u'Ð', '&ETH;'   ],
    [u'Ñ', '&Ntilde;'],  [u'Ò', '&Ograve;'],
    [u'Ó', '&Oacute;'],  [u'Ô', '&Ocirc;' ],
    [u'Õ', '&Otilde;'],  [u'Ö', '&Ouml;'  ],
    [u'×', '&times;' ],  [u'Ø', '&Oslash;'],
    [u'Ù', '&Ugrave;'],  [u'Ú', '&Uacute;'],
    [u'Û', '&Ucirc;' ],  [u'Ü', '&Uuml;'  ],
    [u'Ý', '&Yacute;'],  [u'Þ', '&THORN;' ],
    [u'ß', '&szlig;' ],  [u'à', '&agrave;'],
    [u'á', '&aacute;'],  [u'â', '&acirc;' ],
    [u'ã', '&atilde;'],  [u'ä', '&auml;'  ],
    [u'å', '&aring;' ],  [u'æ', '&aelig;' ],
    [u'ç', '&ccedil;'],  [u'è', '&egrave;'],
    [u'é', '&eacute;'],  [u'ê', '&ecirc;' ],
    [u'ë', '&euml;'  ],  [u'ì', '&igrave;'],
    [u'í', '&iacute;'],  [u'î', '&icirc;' ],
    [u'ï', '&iuml;'  ],  [u'ð', '&eth;'   ],
    [u'ñ', '&ntilde;'],  [u'ò', '&ograve;'],
    [u'ó', '&oacute;'],  [u'ô', '&ocirc;' ],
    [u'õ', '&otilde;'],  [u'ö', '&ouml;'  ],
    [u'÷', '&divide;'],  [u'ø', '&oslash;'],
    [u'ù', '&ugrave;'],  [u'ú', '&uacute;'],
    [u'û', '&ucirc;' ],  [u'ü', '&uuml;'  ],
    [u'ý', '&yacute;'],  [u'þ', '&thorn;' ],
    [u'ÿ', '&yuml;'  ],
]

if __name__ == "__main__":
   text_utf = u"Example of xml encoding: cigüeña"
   text_xml = encode(text_utf)
   print text_xml
   print decode(text_xml)
   
