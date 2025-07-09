/*Readme*/
/*本代码是Web前端Login的js部分*/
/*后端依赖API:https://mqttapi.silence.wiki/api/login*/
/*Readme*/

const ApiAdapter = {
  users: {
    login: async (username, password) => {
      try {
        const response = await fetch('https://mqttapi.silence.wiki/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
          throw new Error('网络响应失败');
        }

        return await response.json();
      } catch (err) {
        return { success: false, message: err.message || '请求失败' };
      }
    },
  },
};

// 登录表单提交处理
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  const loginButton = document.querySelector('.login-button');
  loginButton.disabled = true;
  loginButton.textContent = '登录中...';

  try {
    // 调用API，传入用户名密码
    const result = await ApiAdapter.users.login(username, password);

    if (result.success) {
      if (username === 'user') {
        localStorage.setItem('userRole', 'user');  
        alert('登录成功！');
        window.location.href = 'dashboard.html';
      } else {
        alert('登录失败！');
      }
    } else {
      alert(`登录失败！${result.message || '用户名或密码错误'}`);
    }
  } catch (error) {
    console.error('登录错误:', error);
    alert('登录失败！网络错误，请稍后重试');
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = '登录';
  }
});

// 自动去除用户名空格
document.getElementById('username').addEventListener('input', function () {
  this.value = this.value.trim();
});
