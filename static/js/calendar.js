document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('calendar');
  if (!calendarEl) return; 

  let holidayList = [];
  try {
    holidayList = JSON.parse(calendarEl.dataset.holidays);
  } catch (e) {
    console.warn('Invalid or missing data-holidays:', e);
  }

  const calendar = new FullCalendar.Calendar(calendarEl, {
    locale: 'ja',
    initialView: 'dayGridMonth',
    headerToolbar: { left:'prev,next today', center:'title', right:'' },
    buttonText: { today:'今日', prev: '<', next:'>' },
    firstDay: 0,
    events: '/api/schedules',
    dayCellDidMount: info => {
      const d = info.date.toISOString().slice(0,10);
      if (info.date.getDay() === 0 || holidayList.includes(d)) {
        info.el.classList.add('holiday');
      }
    },
    dateClick: info => {
      window.location.href = `/schedules/date/${info.dateStr}`;
    },
    datesSet: info => {
      fetch(`/api/note_list?start=${info.startStr}&end=${info.endStr}`)
        .then(r => r.json())
        .then(data => {
          // 既存バッジクリア
          calendarEl.querySelectorAll('.fc-note-badge').forEach(el => el.remove());

          // 新規バッジ追加
          (data.note_list || []).forEach(note => {
            const d = note.date;
            const dayCell = calendarEl.querySelector(`.fc-daygrid-day[data-date="${d}"]`);
            if (!dayCell) return;
            const badge = document.createElement('span');
            badge.className = 'fc-note-badge badge bg-warning text-dark';
            badge.textContent = '💬';
            Object.assign(badge.style, {
              position:   'absolute',
              top:        '2px',
              left:       '2px',
              fontSize:   '1rem',
              padding:    '2px 4px',
              lineHeight: '1',
              zIndex:     '10'
            });
            dayCell.style.position = 'relative';
            dayCell.appendChild(badge);
          });
        })
        .catch(e => console.warn('note_list取得失敗', e));
    }
  });

  calendar.render();
});
