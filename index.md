---
layout: default
# title: Home 
---

<h1 class="page-heading">Blog Posts</h1> 

{%- if site.posts.size > 0 -%}
  <ul class="posts"> 
    {%- for post in site.posts limit: 15 -%}
    <li> 
      <span class="post-date-custom">{{ post.date | date: "%d %b %Y" }}</span> 
      <span class="post-separator-custom">&raquo;</span> 
      <a class="post-link-title-custom" href="{{ post.url | relative_url }}">{{ post.title | escape }}</a>
    </li>
    {%- endfor -%}
  </ul>
  {% if site.posts.size > 15 %}
    <p style="margin-top: 1.5em;"><a href="{{ '/archive/' | relative_url }}">View All Posts &rarr;</a></p>
  {% endif %}
{%- endif -%}