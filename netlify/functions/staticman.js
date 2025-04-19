const axios = require('axios');

exports.handler = async function(event, context) {
  const headers = {
    'Access-Control-Allow-Origin': 'https://amosqiang.github.io', // 替换为你的博客域名
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: '',
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: 'Method Not Allowed',
    };
  }

  try {
    const requestBody = JSON.parse(event.body);
    const { name, email, comment } = requestBody;

    const repoOwner = 'Amosqiang';
    const repoName = 'amosqiang.github.io';
    const branch = 'main';
    const commentBranch = `comment-${Date.now()}`;
    const githubToken = process.env.GITHUB_TOKEN;

    const pullRequestUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/pulls`;

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
      headers,
      body: JSON.stringify({ message: 'Pull Request created successfully', prUrl: response.data.html_url }),
    };
  } catch (error) {
    return {
      statusCode: error.response?.status || 500,
      headers,
      body: JSON.stringify({ error: error.message }),
    };
  }
};