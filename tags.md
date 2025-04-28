---
layout: page
#title: All Tags
permalink: /Tags/
---

{% comment %} H1 标题由 layout: page 自动生成，此处无需重复 {% endcomment %}

<div class="tag-list" style="margin-top: 2em;">
  {% assign sorted_tags = site.tags | sort %} 

  {% comment %} 可选：标签云或列表 {% endcomment %}
  <div class="tag-cloud" style="margin-bottom: 3em;">
    <strong>All Tags:</strong><br>
    {% for tag in sorted_tags %}
      {% assign tag_name = tag[0] %}
      {% assign tag_size = tag[1].size %}
      <a href="#{{ tag_name | slugify }}" style="font-size: {{ tag_size | times: 4 | plus: 80 }}%;">{{ tag_name }}</a> {% unless forloop.last %}&nbsp;{% endunless %}
    {% endfor %}
  </div>
  <hr>

  {% comment %} 按标签列出文章 {% endcomment %}
  {% for tag in sorted_tags %}
    {% assign tag_name = tag[0] %}
    {% assign posts_with_tag = tag[1] %}

    <h2 id="{{ tag_name | slugify }}" style="margin-top: 2.5em; margin-bottom: 1em;">
      #{{ tag_name }} 
      <span style="font-size: 0.7em; color: #888;">({{ posts_with_tag | size }} 篇文章)</span>
    </h2>

    <ul class="post-list-for-tag" style="list-style: none; padding-left: 1em;">
      {% for post in posts_with_tag %}
        <li style="margin-bottom: 0.5em;">
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
          <span class="post-date" style="color: #aaa; font-size: 0.8em; margin-left: 0.5em;"> - {{ post.date | date: "%Y-%m-%d" }}</span>
        </li>
      {% endfor %}
    </ul>
  {% endfor %}
</div>

{% comment %} 
说明：
- layout: 指定页面使用的布局文件，请确保 'page' 布局存在或使用您有的布局。
- title: 页面的标题。
- permalink: /tags/ 让这个页面的网址固定为 yoursite.com/tags/。
- site.tags: Jekyll 提供的变量，包含所有标签及其对应的文章列表。
- sort: Liquid 过滤器，用于按字母顺序排序标签。
- tag[0]: 标签的名称。
- tag[1]: 包含该标签的文章数组。
- slugify: Liquid 过滤器，将标签名转换为 URL 友好的格式 (例如 "Web Dev" -> "web-dev")，用于创建锚点链接 (#)。
- id="{{ tag_name | slugify }}": 为每个标签标题创建锚点，这样文章页面的标签链接可以直接跳转到这里。
- 简单的标签云示例代码根据标签下的文章数量调整字体大小。
- 内联样式 <style="...">: 为了快速查看效果添加了简单样式，建议后续将这些样式移到 assets/css/style.scss 文件中进行统一管理。
{% endcomment %}
