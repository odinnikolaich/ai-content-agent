from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render_muse', ROOT/'scripts/muse_render_telegram.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_compact_caption_text_exact(tmp_path):
    script='Измерьте расстояние от дивана до телевизора. Комфорт зависит от диагонали.'
    cues=mod.phrases(script)
    assert ' '.join(cues)==script
    assert all(len(x)<=30 for x in cues)


def test_ass_resolution_and_small_font(tmp_path):
    text='Проверьте качество изображения. Посмотрите на отражения.'
    file=tmp_path/'subtitles.ass'
    report=mod.subtitle_ass(text,voice_duration=4.0,full_duration=6.0,out=file)
    txt=file.read_text(encoding='utf-8-sig')
    assert 'PlayResX: 720' in txt and 'PlayResY: 1280' in txt
    assert 'Style: Clean,Arial,28,' in txt
    assert report['max_characters'] <=30
    assert all(x in txt for x in ['Проверьте','отражения.'])


def test_unverified_video_refuses_assembly(tmp_path):
    p=tmp_path/'pack'
    # No QA imports is a hard failure BEFORE any FFmpeg or Telegram interaction.
    with pytest.raises((OSError,RuntimeError,FileNotFoundError)):
        mod.assemble(p,tmp_path/'video.mp4')


def test_unsafe_subtitle_markup_rejected():
    with pytest.raises(RuntimeError):
        mod.phrases('Тест {\\an8} нечестное изменение места надписи.')