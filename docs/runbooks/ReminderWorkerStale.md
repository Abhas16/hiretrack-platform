# ReminderWorkerStale

**What it means:** the daily `reminder-worker` CronJob hasn't succeeded for 26 hours, so follow-up
reminders aren't being created.

```bash
kubectl -n hiretrack get cronjob hiretrack-reminder-worker
kubectl -n hiretrack get jobs | grep reminder
kubectl -n hiretrack logs job/<latest-job>
```
- `reminder run failed` with a database error → see [ApiNoReadyPods](ApiNoReadyPods.md) step 1.
- No Job created at all → the CronJob is suspended, or the schedule/timeZone is wrong.

Re-run by hand (safe: it never creates duplicate reminders):
```bash
kubectl -n hiretrack create job --from=cronjob/hiretrack-reminder-worker reminders-manual-$(date +%s)
```
