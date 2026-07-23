const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export type User = {id:string; email:string; full_name:string; role:"system_admin"|"admin"|"user"; is_active:boolean};
export type Product = {id:string; code:string; name:string; description?:string; documents:Doc[]};
export type Doc = {id:string; name:string; kind:string; category:string; revision:string; sequence:number; file_name:string};
export type Template = {id:string; name:string; kind:string; revision:string; field_map:Record<string,unknown>; file_name:string};
export type SubmittalAttachment = {id:string; name:string; category:string; sequence:number; sha256:string};
export type Submittal = {id:string; number:string; revision:string; project_name:string; material_description:string; document_order:(string|null)[]; section_order:string[]; project_number?:string; client?:string; consultant?:string; main_contractor?:string; subcontractor?:string; submitted_by?:string; submitted_by_role?:string; submission_date:string; status:string; error_message?:string; final_sha256?:string; products:Product[]; attachments:SubmittalAttachment[]; created_by?:User; created_at:string; generated_at?:string};

class Api {
  token = localStorage.getItem("token");
  async request<T>(path:string, init:RequestInit = {}):Promise<T> {
    const headers = new Headers(init.headers);
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const response = await fetch(`${BASE}${path}`, {...init, headers});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = Array.isArray(body.detail)
        ? body.detail.map((item: {msg?: string}) => item.msg || "Invalid value").join("; ")
        : body.detail;
      throw new Error(detail || "Request failed");
    }
    if (response.status === 204) return undefined as T;
    return response.json();
  }
  async login(email:string,password:string) {
    const body = new URLSearchParams({username:email,password});
    const result = await this.request<{access_token:string;user:User}>("/auth/login", {method:"POST",body,headers:{"Content-Type":"application/x-www-form-urlencoded"}});
    this.token=result.access_token; localStorage.setItem("token",this.token); return result.user;
  }
  logout(){ this.token=null; localStorage.removeItem("token"); }
  async download(id:string) {
    const response = await fetch(`${BASE}/submittals/${id}/download`, {headers:{Authorization:`Bearer ${this.token}`}});
    if (!response.ok) throw new Error("Download failed");
    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || "submittal.pdf";
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.style.display = "none";
    document.body.appendChild(anchor);
    anchor.click();
    setTimeout(() => { anchor.remove(); URL.revokeObjectURL(url); }, 30000);
  }
  async openPdf(collection:"documents"|"templates", id:string) {
    const response = await fetch(`${BASE}/${collection}/${id}/file`, {headers:{Authorization:`Bearer ${this.token}`}});
    if (!response.ok) throw new Error("Unable to open PDF");
    const url = URL.createObjectURL(await response.blob());
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
  async previewSubmittal(id:string) {
    const response = await fetch(`${BASE}/submittals/${id}/preview`, {headers:{Authorization:`Bearer ${this.token}`}});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Preview failed");
    }
    const url = URL.createObjectURL(await response.blob());
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
}
export const api = new Api();
