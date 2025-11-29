### Ⅰ.[Site](https://jekyllrb.com/docs/)

### Ⅱ.Jekyll is a <mark style="background: #FFB86CA6;">static site generator</mark>.

- It takes text written in your favorite markup language and uses layouts to create a static website.
- You can **tweak** the site's **look and feel**, **URLs**, the **data** displayed on the page, and more.

### Ⅲ.Environment requires

- ruby
- RubyGems
- GCC and Make

### Ⅲ.Jekyll Install on macOS

1.  Install \[\[homebrew\]\]
2.  `brew install ruby`
3.  `echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc`
4.  `gem install jekyll`
5.  `echo 'export PATH="/opt/homebrew/lib/ruby/gems/3.3.0/bin:$PATH"' >> ~/.zshrc`
6.  `cd git`
7.  `bundle install`
8.  `bundle update`
9.  `jekyll serve`
10. `control c`：暂停
11. year-month-day-name.md

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
