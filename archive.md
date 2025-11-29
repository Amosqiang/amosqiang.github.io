---
layout: page # 你可以使用 'page' 布局，或者 'default' 布局
#title: Blog Archive
permalink: /archive/ # 明确指定 URL 路径为 /archive/ (可选, 但推荐)
---

<h1>{{ page.title }}</h1>

<p>Here are all the posts in chronological order.</p>

<ul class="post-list-compact" style="list-style: none; padding-left: 0;">
  {% comment %} 循环输出所有文章 site.posts {% endcomment %}
  {% for post in site.posts %}
    <li style="margin-bottom: 0.8em;">
      <span class="post-meta" style="color: #888; font-size: 0.9em;">{{ post.date | date: "%Y-%m-%d" }}</span> &raquo;
      <a class="post-link" href="{{ post.url | relative_url }}">{{ post.title | escape }}</a>
    </li>
  {% endfor %}
</ul>
