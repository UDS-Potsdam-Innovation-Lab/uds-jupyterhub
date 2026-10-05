import os, sys
c = get_config()

# --- Hub storage (survives redeploys) ---
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/data/jupyterhub.sqlite"
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub/data/jupyterhub_cookie_secret"

# --- Networking ---
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = "jupyterhub-hub"

# --- Protect the other apps on this server ---
c.JupyterHub.active_server_limit = int(os.environ.get("MAX_ACTIVE", "15"))

# --- One container per student ---
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = os.environ["NOTEBOOK_IMAGE"]
c.DockerSpawner.network_name = "jupyterhub-net"
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.remove = True
c.DockerSpawner.notebook_dir = "/home/jovyan/work"
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": "/home/jovyan/work"}
c.DockerSpawner.mem_limit = "1G"
c.DockerSpawner.cpu_limit = 1.0
c.DockerSpawner.extra_host_config = {"pids_limit": 512}
c.Spawner.default_url = "/lab"
c.Spawner.start_timeout = 120

# --- Login ---
admins = {u.strip() for u in os.environ.get("ADMIN_USERS", "").split(",") if u.strip()}
c.Authenticator.admin_users = admins

if os.environ.get("AUTH_MODE", "test") == "lti":
    moodle = os.environ["MOODLE_URL"].rstrip("/")
    c.JupyterHub.authenticator_class = "ltiauthenticator.lti13.auth.LTI13Authenticator"
    c.LTI13Authenticator.issuer = moodle
    c.LTI13Authenticator.authorize_url = f"{moodle}/mod/lti/auth.php"
    c.LTI13Authenticator.jwks_endpoint = f"{moodle}/mod/lti/certs.php"
    c.LTI13Authenticator.client_id = [os.environ["LTI_CLIENT_ID"]]
    c.LTI13Authenticator.username_key = "email"
    c.Authenticator.allow_all = True
else:
    # Temporary test login: any username in ADMIN_USERS + TEST_PASSWORD
    c.JupyterHub.authenticator_class = "dummy"
    c.DummyAuthenticator.password = os.environ["TEST_PASSWORD"]
    c.Authenticator.allowed_users = admins

# --- Stop idle student servers after 1 hour ---
c.JupyterHub.load_roles = [{
    "name": "idle-culler",
    "scopes": ["list:users", "read:users:activity", "read:servers", "delete:servers"],
    "services": ["idle-culler"],
}]
c.JupyterHub.services = [{
    "name": "idle-culler",
    "command": [sys.executable, "-m", "jupyterhub_idle_culler", "--timeout=3600"],
}]
