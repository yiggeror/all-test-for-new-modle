// Visibility rasterizer for authored edges over Blender cloth/face clay renders.
// Input: uint32 W,H,Ntriangle,Nedge, then float x,y,depth tuples (3 per tri, 2 per edge).
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <vector>
struct V{float x,y,z;};
static float cross(float x,float y,float x2,float y2){return x*y2-y*x2;}
int main(int argc,char**argv){
 if(argc!=3) return 2;
 std::ifstream in(argv[1],std::ios::binary);
 uint32_t w,h,nt,ne;
 in.read((char*)&w,4);in.read((char*)&h,4);in.read((char*)&nt,4);in.read((char*)&ne,4);
 if(!in||w==0||h==0||w>6000||h>6000||!nt||!ne) return 3;
 const float inf=std::numeric_limits<float>::infinity();
 std::vector<float> zbuf(size_t(w)*h,inf);
 auto lx=[&](float x){return std::clamp(int(std::floor(x)),0,int(w)-1);};
 auto ly=[&](float y){return std::clamp(int(std::floor(y)),0,int(h)-1);};
 for(uint32_t j=0;j<nt;j++){
  V v[3]; in.read((char*)v,sizeof v);
  float abx=v[1].x-v[0].x,aby=v[1].y-v[0].y,acx=v[2].x-v[0].x,acy=v[2].y-v[0].y,det=cross(abx,aby,acx,acy);
  if(std::abs(det)<1e-10f) continue;
  int x0=lx(std::min({v[0].x,v[1].x,v[2].x})),x1=lx(std::max({v[0].x,v[1].x,v[2].x})), y0=ly(std::min({v[0].y,v[1].y,v[2].y})), y1=ly(std::max({v[0].y,v[1].y,v[2].y}));
  for(int y=y0;y<=y1;y++) for(int x=x0;x<=x1;x++){
   float dx=x+.5f-v[0].x,dy=y+.5f-v[0].y,u=cross(dx,dy,acx,acy)/det,vv=cross(abx,aby,dx,dy)/det;
   if (u>=-.00001f && vv>=-.00001f && u+vv<=1.00001f){
    float t=v[0].z*(1.f-u-vv)+v[1].z*u+v[2].z*vv;
    auto i=size_t(y)*w+x;if(t<zbuf[i])zbuf[i]=t;
   }
  }
 }
 std::vector<uint8_t> mask(size_t(w)*h,0);
 for(uint32_t j=0;j<ne;j++){
  V v[2];in.read((char*)v,sizeof v);
  float ax=v[0].x,ay=v[0].y,dx=v[1].x-ax,dy=v[1].y-ay;
  float length=dx*dx+dy*dy;if(length<1e-7f)continue;
  int x0=lx(std::min(ax,v[1].x)-2),x1=lx(std::max(ax,v[1].x)+2),y0=ly(std::min(ay,v[1].y)-2),y1=ly(std::max(ay,v[1].y)+2);
  for(int y=y0;y<=y1;y++) for(int x=x0;x<=x1;x++){
   float rx=x+.5f-ax,ry=y+.5f-ay;
   float t=std::clamp((rx*dx+ry*dy)/length,0.f,1.f),dist=std::hypot(rx-dx*t,ry-dy*t);
   if (dist>1.26f) continue;
   auto i=size_t(y)*w+x;
   float z=v[0].z*(1.f-t)+v[1].z*t;
   // Subdivision control points are reprojected to the actual evaluated surface before this test.
   if(std::isfinite(zbuf[i]) && z<=zbuf[i]+.00135f && z>=zbuf[i]-.010f){
    uint8_t opacity=uint8_t(std::clamp((1.26f-dist)*139.f,0.f,152.f));
    mask[i]=std::max(mask[i],opacity);
   }
  }
 }
 if(!in)return 4;
 std::ofstream out(argv[2],std::ios::binary);
 out<<"P5\n"<<w<<" "<<h<<"\n255\n"; out.write((char*)mask.data(),mask.size());
 return out ? 0 : 5;
}
