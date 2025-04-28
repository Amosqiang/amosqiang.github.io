---
layout: page 
#title: All Categories
permalink: /Categories/
---

{% comment %} H1 标题由 layout: page 自动生成，此处无需重复 {% endcomment %}

<div class="category-list" style="margin-top: 2em;">
  {% assign sorted_categories = site.categories | sort %} 

  {% comment %} 可选：分类导航 {% endcomment %}
  <div class="category-links" style="margin-bottom: 3em;">
    <strong>All Categories:</strong><br>
     {% for category in sorted_categories %}
        {% assign category_name = category[0] %}
        <a href="#{{ category_name | slugify }}">{{ category_name }}</a>{% unless forloop.last %} | {% endunless %}
      {% endfor %}
  </div>
  <hr>

  {% comment %} 按分类列出文章 {% endcomment %}
  {% for category in sorted_categories %}
    {% assign category_name = category[0] %}
    {% assign posts_with_category = category[1] %}

    <h2 id="{{ category_name | slugify }}" style="margin-top: 2.5em; margin-bottom: 1em;">
      #{{ category_name }} 
      <span style="font-size: 0.7em; color: #888;">({{ posts_with_category | size }} 篇文章)</span>
    </h2>

    <ul class="post-list-for-category" style="list-style: none; padding-left: 1em;">
      {% for post in posts_with_category %}
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
- permalink: /categories/ 让这个页面的网址固定为 yoursite.com/categories/。
- site.categories: Jekyll 提供的变量，包含所有分类及其对应的文章列表。
- 其余逻辑与 tags.md 类似。
{% endcomment %}
