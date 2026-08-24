import { useEffect, useState } from "react";
import { ActionSheet, Button, Card, Form, Image, Input, List, Space, TextArea, Toast } from "antd-mobile";
import type { Condition, EventDraft, EventType, FeedOutcome } from "../../entities/event/model";
import { useHerpSnapshot, useHerpStore } from "../../app/store-context";
import { petFallbackImage } from "../../shared/pet-image";

interface RecordFeatureProps {
  initialPetId?: string;
  initialType?: EventType;
}

const typeOptions = [
  { label: "喂食", value: "feed", description: "记录吃了什么、吃了多少" },
  { label: "体重", value: "weight", description: "更新当前体重" },
  { label: "排泄", value: "poop", description: "记录排泄状态" },
  { label: "蜕皮", value: "shed", description: "记录本次蜕皮" },
  { label: "照片", value: "photo", description: "留下成长记录" },
] as const;

/**
 * 单宠物单动作记录：页面始终只展示一个宠物和一种事件表单，避免误操作。
 * 输入：可选的 initialPetId 与 initialType 用于今日待办预选；保存后保留当前上下文并提示成功。
 */
export function RecordFeature({ initialPetId, initialType }: RecordFeatureProps) {
  const store = useHerpStore();
  const { pets } = useHerpSnapshot();
  const validPetId = pets.some((pet) => pet.id === initialPetId) ? initialPetId! : pets[0]?.id ?? "";
  const [petId, setPetId] = useState(validPetId);
  const [type, setType] = useState<EventType>(initialType && typeOptions.some((option) => option.value === initialType) ? initialType : "feed");
  const [petSheetVisible, setPetSheetVisible] = useState(false);
  const [typeSheetVisible, setTypeSheetVisible] = useState(false);
  const [outcome, setOutcome] = useState<FeedOutcome>("ate");
  const [condition, setCondition] = useState<Condition>("normal");
  const [food, setFood] = useState("冻鼠");
  const [amountGram, setAmountGram] = useState("18");
  const [weightGram, setWeightGram] = useState("");
  const [note, setNote] = useState("");
  const pet = pets.find((candidate) => candidate.id === petId);
  const selectedType = typeOptions.find((option) => option.value === type) ?? typeOptions[0];

  useEffect(() => {
    const latest = store.getLatestEvent(petId, type);
    setOutcome(latest?.outcome ?? "ate");
    setCondition(latest?.condition ?? "normal");
    setFood(latest?.food ?? "冻鼠");
    setAmountGram(String(latest?.amountGram ?? 18));
    setWeightGram(latest?.weightGram ? String(latest.weightGram) : "");
    setNote("");
  }, [petId, type]);

  function saveRecord(): void {
    const base: EventDraft = { petId, type, occurredAt: new Date(), note: note.trim() };
    if (type === "feed") {
      const amount = Number(amountGram);
      if (!food.trim()) {
        Toast.show({ content: "请填写食物" });
        return;
      }
      if (amount <= 0) {
        Toast.show({ content: "请填写有效重量" });
        return;
      }
      base.outcome = outcome;
      base.food = food.trim();
      base.amountGram = amount;
    }
    if (type === "weight") {
      const weight = Number(weightGram);
      if (weight <= 0) {
        Toast.show({ content: "请填写有效体重" });
        return;
      }
      base.weightGram = weight;
    }
    if (type === "poop" || type === "shed") base.condition = condition;
    store.saveEvent(base);
    Toast.show({ content: "已保存" });
  }

  if (!pet) return null;

  return (
    <Space block direction="vertical" style={{ "--gap": "14px" }}>
      <div className="record-page-intro">
        <span className="eyebrow">FIELD NOTE</span>
        <h1>记下这一刻</h1>
        <p>只记录一只宠物的一件事。</p>
      </div>
      <Card className="record-context-card">
        <div className="record-context">
          <Image src={pet.photoUrl ?? petFallbackImage} fit="cover" className="record-pet-image" />
          <div className="record-context-copy"><span>正在记录</span><strong>{pet.name}</strong><small>{pet.species} · {pet.morph}</small></div>
          <Button size="small" fill="none" onClick={() => setPetSheetVisible(true)}>更换</Button>
        </div>
      </Card>
      <Card title={selectedType.label} extra={<Button size="small" fill="none" onClick={() => setTypeSheetVisible(true)}>更换动作</Button>}>
        <p className="record-action-hint">{selectedType.description}</p>
        <Form layout="horizontal">
          {type === "feed" && <>
            <Form.Item label="结果"><div className="record-choice-row"><Button color={outcome === "ate" ? "primary" : "default"} onClick={() => setOutcome("ate")}>吃了</Button><Button color={outcome === "refused" ? "danger" : "default"} onClick={() => setOutcome("refused")}>拒食</Button></div></Form.Item>
            <Form.Item label="食物" required><Input value={food} onChange={setFood} placeholder="例如：冻鼠" /></Form.Item>
            <Form.Item label="重量" required><Input type="number" value={amountGram} onChange={setAmountGram} placeholder="克" /></Form.Item>
          </>}
          {type === "weight" && <Form.Item label="体重" required><Input type="number" value={weightGram} onChange={setWeightGram} placeholder="输入当前克数" /></Form.Item>}
          {(type === "poop" || type === "shed") && <Form.Item label="状态"><div className="record-choice-row"><Button color={condition === "normal" ? "primary" : "default"} onClick={() => setCondition("normal")}>正常</Button><Button color={condition === "abnormal" ? "danger" : "default"} onClick={() => setCondition("abnormal")}>异常</Button></div></Form.Item>}
          {(type === "photo" || condition === "abnormal" || type === "feed" || type === "weight") && <Form.Item label="备注"><TextArea value={note} onChange={setNote} placeholder="写点什么，可不填" /></Form.Item>}
        </Form>
        <Button block color="primary" size="large" onClick={saveRecord}>保存这条记录</Button>
      </Card>
      <List header="接下来可以记录">
        <List.Item onClick={() => setTypeSheetVisible(true)} clickable>换一个动作</List.Item>
      </List>
      <ActionSheet visible={petSheetVisible} actions={pets.map((candidate) => ({ key: candidate.id, text: `${candidate.name} · ${candidate.species}` }))} cancelText="取消" onClose={() => setPetSheetVisible(false)} onAction={(action) => { setPetId(String(action.key)); setPetSheetVisible(false); }} />
      <ActionSheet visible={typeSheetVisible} actions={typeOptions.map((option) => ({ key: option.value, text: option.label }))} cancelText="取消" onClose={() => setTypeSheetVisible(false)} onAction={(action) => { setType(action.key as EventType); setTypeSheetVisible(false); }} />
    </Space>
  );
}
