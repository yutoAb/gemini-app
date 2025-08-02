"use client";

import { useState, useRef } from "react";
import useSWR from "swr";
import {
  Stack,
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import { fetcher } from "../../hooks/fetcher";

type Item = {
  id: number;
  name: string;
};

const API_BASE_URL = "http://localhost:5000";

export default function Home() {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const {
    data: items,
    mutate,
    isLoading,
    error,
  } = useSWR<Item[]>(`${API_BASE_URL}/items`, fetcher);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        await fetch(`${API_BASE_URL}/upload-audio`, {
          method: "POST",
          body: formData,
        });

        mutate();
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      console.error("マイクへのアクセスに失敗しました:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  if (isLoading) return <Typography>読み込み中...</Typography>;
  if (error) return <Typography>エラーが発生しました。</Typography>;

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        mt: 5,
      }}
    >
      <Box sx={{ width: "60%", bgcolor: "background.paper", p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Gemini Voice App
        </Typography>

        <Stack spacing={2} direction="row" mb={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={startRecording}
            disabled={recording}
          >
            録音開始
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={stopRecording}
            disabled={!recording}
          >
            録音停止・送信
          </Button>
        </Stack>

        <Typography variant="h6" gutterBottom>
          応答履歴
        </Typography>
        <List>
          {items?.map((item, index) => (
            <ListItem key={index}>
              <ListItemText primary={item.name} />
            </ListItem>
          ))}
        </List>
      </Box>
    </Box>
  );
}
