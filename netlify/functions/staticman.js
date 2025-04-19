const axios = require('axios');

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: 'Method Not Allowed',
    };
  }

  const requestBody = JSON.parse(event.body);
  const { name, email, comment } = requestBody;

  const repoOwner = 'Amosqiang'; // 替换为您的 GitHub 用户名
  const repoName = 'amosqiang.github.io'; // 替换为您的仓库名称
  const branch = 'main'; // 目标分支，通常为 'main' 或 'master'
  const commentBranch = `comment-${Date.now()}`; // 创建一个唯一的分支名

  const githubToken = process.env.GITHUB_TOKEN; // 确保在环境变量中设置了 GITHUB_TOKEN

  // 创建包含评论的分支并提交更改的逻辑应在此处实现
  // 这通常涉及使用 GitHub API 创建分支、添加文件、提交更改等操作

  const pullRequestUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/pulls`;

  try {
    const response = await axios.post(
      pullRequestUrl,
      {
        title: 'New Comment',
        head: commentBranch,
        base: branch,
        body: `Name: ${name}\nEmail: ${email}\nComment: ${comment}`,
      },
      {
        headers: {
          Authorization: `token ${githubToken}`,
          'User-Agent': 'Netlify Function',
          Accept: 'application/vnd.github.v3+json',
        },
      }
    );

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Pull Request created successfully', prUrl: response.data.html_url }),
    };
  } catch (error) {
    return {
      statusCode: error.response?.status || 500,
      body: JSON.stringify({ error: error.message }),
    };
  }
};

