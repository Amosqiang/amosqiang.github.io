<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" indent="yes" encoding="utf-8"/>

  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title><xsl:value-of select="rss/channel/title"/></title>
        <style>
          body { font-family: Georgia, "Times New Roman", serif; margin: 2rem; color: #1c1c1c; background: #fafafa; }
          .wrap { max-width: 800px; margin: 0 auto; }
          h1 { font-size: 1.8rem; margin: 0 0 0.5rem; }
          .meta { color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }
          .item { padding: 1rem 0; border-bottom: 1px solid #e2e2e2; }
          .item:last-child { border-bottom: 0; }
          .title { font-size: 1.1rem; font-weight: 700; margin: 0 0 0.35rem; }
          .title a { color: #1c1c1c; text-decoration: none; }
          .title a:hover { text-decoration: underline; }
          .date { color: #777; font-size: 0.85rem; margin-bottom: 0.4rem; }
          .desc { font-size: 0.98rem; line-height: 1.6; color: #333; }
        </style>
      </head>
      <body>
        <div class="wrap">
          <h1><xsl:value-of select="rss/channel/title"/></h1>
          <div class="meta">
            RSS feed view. You can subscribe with your reader using the XML URL.
          </div>
          <xsl:for-each select="rss/channel/item">
            <div class="item">
              <div class="title">
                <a>
                  <xsl:attribute name="href">
                    <xsl:value-of select="link"/>
                  </xsl:attribute>
                  <xsl:value-of select="title"/>
                </a>
              </div>
              <div class="date"><xsl:value-of select="pubDate"/></div>
              <div class="desc"><xsl:value-of select="description"/></div>
            </div>
          </xsl:for-each>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
