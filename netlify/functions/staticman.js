const axios = require('axios');

exports.handler = async function(event, context) {
  // 只有在 POST 请求时，才会处理评论
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405, // Method Not Allowed
      body: 'Method Not Allowed',
    };
  }

  const requestBody = JSON.parse(event.body);

  // 从请求体中获取评论数据
  const { name, email, comment } = requestBody;

  // 你需要替换的 GitHub 仓库的信息
  const repoOwner = 'your-github-username'; // 例如：'Amosqiang'
  const repoName = 'your-repo-name'; // 你的仓库名称
  const branch = 'main'; // 使用的分支，通常是 `main` 或 `master`

  const pullRequestUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/pulls`;

  try {
    // 创建 Pull Request 提交评论
    const response = await axios.post(pullRequestUrl, {
      title: 'New Comment',
      head: `comment-${Date.now()}`, // PR的头部，确保唯一
      base: branch,
      body: `Name: ${name}\nEmail: ${email}\nComment: ${comment}`,
    }, {
      headers: {
        Authorization: `token ${process.env.GITHUB_TOKEN}`, // 你的 GitHub Token
      },
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Comment submitted successfully!',
        pullRequest: response.data.html_url, // 提交的PR链接
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'There was an error submitting the comment.' }),
    };
  }
};
