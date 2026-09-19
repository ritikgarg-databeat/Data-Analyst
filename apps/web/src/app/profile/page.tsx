"use client";

import { useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { currentUserQueryKey } from "@/features/users/use-current-user";
import { apiClient } from "@/lib/api-client";

export default function ProfilePage(){const {user,logout}=useAuth();const qc=useQueryClient();
 const [name,setName]=useState(user?.name??"");const [email,setEmail]=useState(user?.email??"");const [password,setPassword]=useState("");const [message,setMessage]=useState("");
 async function saveName(event:FormEvent){event.preventDefault();try{await apiClient.patch("/users/me",{name});await qc.invalidateQueries({queryKey:currentUserQueryKey});setMessage("Profile saved.")}catch(e){setMessage(e instanceof Error?e.message:"Save failed.")}}
 async function saveEmail(event:FormEvent){event.preventDefault();try{await apiClient.post("/auth/change-email",{new_email:email,current_password:password});await logout()}catch(e){setMessage(e instanceof Error?e.message:"Email change failed.")}}
 return <div className="mx-auto max-w-2xl space-y-5"><div><h1 className="text-2xl font-semibold">Profile and security</h1><p className="text-muted-foreground">Manage your account without affecting other users.</p></div>{message?<p role="status" className="text-sm">{message}</p>:null}
 <Card><CardHeader><CardTitle>Profile</CardTitle></CardHeader><CardContent><form className="flex gap-3" onSubmit={saveName}><Input aria-label="Name" value={name} onChange={e=>setName(e.target.value)}/><Button>Save</Button></form></CardContent></Card>
 <Card><CardHeader><CardTitle>Email</CardTitle></CardHeader><CardContent><form className="space-y-3" onSubmit={saveEmail}><div><Label htmlFor="profile-email">Email</Label><Input id="profile-email" type="email" value={email} onChange={e=>setEmail(e.target.value)}/></div><div><Label htmlFor="profile-password">Current password</Label><Input id="profile-password" type="password" value={password} onChange={e=>setPassword(e.target.value)}/></div><Button>Change email and sign out</Button></form></CardContent></Card>
 <Card><CardHeader><CardTitle>Password and sessions</CardTitle></CardHeader><CardContent className="flex gap-2"><Button asChild variant="outline"><a href="/change-password">Change password</a></Button><Button variant="outline" onClick={()=>logout(true)}>Log out all devices</Button></CardContent></Card></div>}
