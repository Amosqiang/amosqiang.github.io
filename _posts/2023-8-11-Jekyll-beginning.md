### Ⅰ.[Site](https://jekyllrb.com/docs/)

### Ⅱ.Jekyll is a <mark style="background: #FFB86CA6;">static site generator</mark>. 
* It takes text written in your favorite markup language and uses layouts to create a static website.
* You can **tweak** the site’s **look and feel**, **URLs**, the **data** displayed on the page, and more.

### Ⅲ.Environment requires
* Ruby version **2.5.0** or higher
* RubyGems
* GCC and Make

### Ⅲ.Jekyll Install on macOS
1. Install [[homebrew]]
2. ``brew install chruby ruby-install xz``
3. ``brew install ruby``
4. ``echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc``
5. ``export LDFLAGS="-L/opt/homebrew/opt/ruby/lib``
6. ``export CPPFLAGS="-I/opt/homebrew/opt/ruby/include"``
7. ``gem install jekyll``
8. ``gem update``
9. ``cd git`` 
10. ``bundle init``
11. <mark style="background: #FFB86CA6;">``jekyll new myblog``</mark> must in gemfile path
12. ``jekyll serve``
13. ``control c``：暂停


### Ⅳ.Jekyll Ecosystem

- **Jekyll**
  - **Static site generator**
  - Transforms text files into websites
  - Works with GitHub Pages

- **Gems**
  - **Ruby's software packages**
  - Provides functionalities for Ruby programs
  - **Jekyll itself is a gem**

- **Gemfile**
  - **Lists** gem dependencies for Ruby projects
  - Ensures consistent gem versions
  - Used by Bundler to manage gems

- **Bundler**
  - **Manages gems specified in the Gemfile**
  - Prevents version conflicts
  - Commands: `bundle install`, `bundle exec jekyll serve`


