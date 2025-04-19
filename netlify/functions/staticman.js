const YAML = require('js-yaml');

exports.handler = async function(event, context) {
  let Octokit;
  try {
    const octokitModule = await import("@octokit/rest");
    Octokit = octokitModule.Octokit;
  } catch (error) {
    console.error("Error importing @octokit/rest:", error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: "Failed to import @octokit/rest" }),
    };
  }

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
    const { name, email, comment, slug } = requestBody; // 确保前端发送了 slug

    const repoOwner = 'Amosqiang';
    const repoName = 'amosqiang.github.io';
    const branch = 'main';
    const commentBranch = `refs/heads/comment-${Date.now()}`;
    const filePath = `_data/comments/${slug}/${Date.now()}.yml`; // 根据你的 Jekyll 配置
    const githubToken = process.env.GITHUB_TOKEN;
    const octokit = new Octokit({ auth: githubToken });

    // 1. 获取 base 分支的 ref
    const baseRef = await octokit.git.getRef({
      owner: repoOwner,
      repo: repoName,
      ref: `heads/${branch}`,
    });
    const baseSha = baseRef.data.object.sha;

    // 2. 创建 blob (文件内容)
    const commentData = { name, email, comment, date: new Date().toISOString() };
    const fileContent = YAML.stringify(commentData);

    const blobResponse = await octokit.git.createBlob({
      owner: repoOwner,
      repo: repoName,
      content: fileContent,
      encoding: 'utf-8',
    });
    const blobSha = blobResponse.data.sha;

    // 3. 创建 tree (包含 blob 的目录结构)
    const treeResponse = await octokit.git.createTree({
      owner: repoOwner,
      repo: repoName,
      base_tree: baseSha,
      tree: [
        {
          path: filePath,
          mode: '100644',
          type: 'blob',
          sha: blobSha,
        },
      ],
    });
    const treeSha = treeResponse.data.sha;

    // 4. 创建 commit
    const commitResponse = await octokit.git.createCommit({
      owner: repoOwner,
      repo: repoName,
      message: 'Add new comment',
      tree: treeSha,
      parents: [baseSha],
    });
    const commitSha = commitResponse.data.sha;

    // 5. 创建新的分支
    await octokit.git.createRef({
      owner: repoOwner,
      repo: repoName,
      ref: commentBranch,
      sha: commitSha,
    });

    // 6. 创建 Pull Request
    const prResponse = await octokit.pulls.create({
      owner: repoOwner,
      repo: repoName,
      title: `New comment on ${slug}`,
      head: commentBranch.replace('refs/heads/', ''),
      base: branch,
      body: `Name: ${name}\nEmail: ${email}\nComment:\n${comment}`,
    });

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ message: 'Comment submitted successfully!', prUrl: prResponse.data.html_url }),
    };
  } catch (error) {
    console.error('Error creating comment:', error);
    return {
      statusCode: error.response?.status || 500,
      headers,
      body: JSON.stringify({ error: error.message }),
    };
  }
};