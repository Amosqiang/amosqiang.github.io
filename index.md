---
layout: default
#title: Home # 保持注释掉，如果你不想要 "Home" 标题
---

{% comment %} 这里可以放你的欢迎语或其他非文章列表内容，如果需要的话 {% endcomment %}
{% comment %} <p>Welcome!</p> <hr> {% endcomment %}

<h4>Recent Posts</h4> 

{% comment %} 这是新的紧凑列表容器 {% endcomment %}
<div class="writing-list">

  {% comment %} 循环输出文章，可以调整 limit 数量 {% endcomment %}
  {% for post in site.posts limit:15 %} 

    {% comment %} 文章标题链接，占第一列 {% endcomment %}
    <div><a href="{{ post.url | relative_url }}" title="{{ post.title | escape }}">{{ post.title | escape }}</a></div>

    {% comment %} 文章日期，占第二列 {% endcomment %}
    <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y-%m-%d" }}</time>

  {% endfor %}

</div> 

{% comment %} 指向归档页的链接 {% endcomment %}
{% if site.posts.size > 15 %} {# 这里的数字要和上面 limit 匹配 #}
  <p style="margin-top: 1.5em;"><a href="/archive/">View All Posts &rarr;</a></p>
{% endif %}