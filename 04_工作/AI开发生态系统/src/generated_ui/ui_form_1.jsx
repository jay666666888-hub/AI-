import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log({ email, password });
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-5">
          <div className="card shadow">
            <div className="card-body p-5">
              <h3 className="text-center mb-4">欢迎登录</h3>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">邮箱</label>
                  <input
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="请输入邮箱"
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">密码</label>
                  <input
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                  />
                </div>
                <button type="submit" className="btn btn-primary w-100 mt-3">
                  登录
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}