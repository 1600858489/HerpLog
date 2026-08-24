import { useState } from "react";
import { Card, Image, List, Popup, Space, Tag } from "antd-mobile";
import type { PetSummary } from "../../entities/pet/model";
import { useHerpSnapshot } from "../../app/store-context";
import { petFallbackImage } from "../../shared/pet-image";

const statusText = { normal: "状态稳定", observe: "观察中", brumation: "冬化中" } as const;

/**
 * 宠物档案：展示照片、基础资料、相册摘要和主人的记录。
 * 用法：点击宠物卡片打开档案 Popup；事件历史统一在时间线页面查看。
 */
export function PetsFeature() {
  const { pets, events } = useHerpSnapshot();
  const [selectedPet, setSelectedPet] = useState<PetSummary | null>(null);
  const selectedPhotos = selectedPet
    ? events.filter((event) => event.petId === selectedPet.id && event.type === "photo")
    : [];

  return (
    <Space block direction="vertical" style={{ "--gap": "14px" }}>
      <div className="pet-page-intro">
        <span className="eyebrow">MY TERRARIUM</span>
        <h1>我的爬宠</h1>
        <p>每一只，都有自己的故事。</p>
      </div>
      <div className="pet-card-grid">
        {pets.map((pet) => (
          <Card key={pet.id} className="pet-profile-card" onClick={() => setSelectedPet(pet)}>
            <Image src={pet.photoUrl ?? petFallbackImage} fallback={petFallbackImage} fit="cover" className="pet-profile-image" />
            <div className="pet-profile-body">
              <div className="pet-profile-heading">
                <div><h2>{pet.name}</h2><span>{pet.species}</span></div>
                <Tag color={pet.status === "observe" ? "warning" : pet.status === "brumation" ? "default" : "success"}>{statusText[pet.status]}</Tag>
              </div>
              <div className="pet-profile-meta">{pet.morph} · {pet.latestWeightGram ?? "-"}g · 下一步：{pet.nextCareText}</div>
            </div>
          </Card>
        ))}
      </div>
      <Popup visible={selectedPet !== null} onMaskClick={() => setSelectedPet(null)} position="bottom" bodyStyle={{ borderTopLeftRadius: 20, borderTopRightRadius: 20 }}>
        {selectedPet && (
          <div className="pet-detail-sheet">
            <Image src={selectedPet.photoUrl ?? petFallbackImage} fallback={petFallbackImage} fit="cover" className="pet-detail-image" />
            <Space block direction="vertical" style={{ "--gap": "16px" }}>
              <div><span className="eyebrow">PET PROFILE</span><h2>{selectedPet.name}</h2><p>{selectedPet.species} · {selectedPet.morph}</p></div>
              <List header="基础资料">
                <List.Item extra={selectedPet.bloodline ?? "未记录"}>血统</List.Item>
                <List.Item extra={selectedPet.morph}>变异</List.Item>
                <List.Item extra={selectedPet.hatchDate ?? "未记录"}>出生日期</List.Item>
                <List.Item extra={selectedPet.breeder ?? "未记录"}>来源</List.Item>
              </List>
              <List header={`相册 · ${selectedPhotos.length} 条记录`}>
                {selectedPhotos.length > 0 ? selectedPhotos.map((photo) => <List.Item key={photo.id}>{photo.note || "成长照片"}</List.Item>) : <List.Item>还没有照片记录</List.Item>}
              </List>
              <Card title="主人的碎碎念">{selectedPet.ownerNote ?? "还没有写下什么。"}</Card>
            </Space>
          </div>
        )}
      </Popup>
    </Space>
  );
}
