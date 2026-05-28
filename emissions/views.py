from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import EmissionRecord, UploadBatch
from .parsers.sap import process_sap
from .parsers.utility import process_utility
from .parsers.travel import process_travel
from django.views.decorators.csrf import csrf_exempt


# ─── ROLE HELPERS ───────────────────────────────────────

def is_admin(user):
    return user.groups.filter(name='Admin').exists() or user.is_superuser

def is_analyst(user):
    return user.groups.filter(name='Analyst').exists() or is_admin(user)

def get_user_org(user):
    try:
        return user.userprofile.organization
    except:
        return None
    
# ─── AUTH ───────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        request.session.save()
        return Response({
            'message': 'Login successful',
            'username': user.username,
            'role': 'admin' if is_admin(user) else 'analyst',
        })
    return Response({'error': 'Invalid credentials'}, status=401)


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out'})


# ─── UPLOAD ─────────────────────────────────────────────

def handle_upload(request, source, process_fn):
    if not is_analyst(request.user):
        return Response({'error': 'Permission denied'}, status=403)

    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=400)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        return Response({'error': 'Only CSV files accepted'}, status=400)

    if file.size == 0:
        return Response({'error': 'File is empty'}, status=400)

    if file.size > 50 * 1024 * 1024:
        return Response({'error': 'File too large. Max 50MB'}, status=400)

    already_exists = UploadBatch.objects.filter(
        filename=file.name,
        source=source
    ).exists()

    if already_exists:
        return Response({
            'error': f'{file.name} already uploaded. Delete existing batch first.'
        }, status=400)

    try:
        records = process_fn(file)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    batch = UploadBatch.objects.create(
        organization=get_user_org(request.user),
        source=source,
        filename=file.name,
        uploaded_by=request.user if request.user.is_authenticated else None,total_rows=len(records),
        failed_rows=sum(1 for r in records if r['status'] == 'failed'),
        suspicious_rows=sum(1 for r in records if r['status'] == 'suspicious'),
    )

    for r in records:
        EmissionRecord.objects.create(
            batch=batch,
            source_row_number=r['source_row_number'],
            source=r['source'],
            scope=r['scope'],
            date=r['date'],
            description=r['description'],
            quantity=r['quantity'],
            unit=r['unit'],
            status=r['status'],
            validation_errors=r['validation_errors'],
            analysis_flags=r['analysis_flags'],
            transformations=r['transformations'],
            raw_data=r['raw_data'],
        )

    clean = batch.total_rows - batch.failed_rows - batch.suspicious_rows

    return Response({
        'batch_id': batch.id,
        'filename': file.name,
        'total': batch.total_rows,
        'failed': batch.failed_rows,
        'suspicious': batch.suspicious_rows,
        'clean': clean,
    })


@csrf_exempt
@api_view(['POST'])
def upload_sap(request):
    return handle_upload(request, 'SAP', process_sap)

@csrf_exempt
@api_view(['POST'])
def upload_utility(request):
    return handle_upload(request, 'UTILITY', process_utility)

@csrf_exempt
@api_view(['POST'])
def upload_travel(request):
    return handle_upload(request, 'TRAVEL', process_travel)


# ─── DASHBOARD ──────────────────────────────────────────

@api_view(['GET'])
def get_batches(request):
    org = get_user_org(request.user)
    batches = UploadBatch.objects.filter(organization=org).order_by('-uploaded_at') if org else UploadBatch.objects.all().order_by('-uploaded_at')
    data = []
    for b in batches:
        clean = b.total_rows - b.failed_rows - b.suspicious_rows
        data.append({
            'id': b.id,
            'source': b.source,
            'filename': b.filename,
            'uploaded_by': b.uploaded_by.username if b.uploaded_by else '',
            'uploaded_at': b.uploaded_at,
            'total_rows': b.total_rows,
            'failed_rows': b.failed_rows,
            'suspicious_rows': b.suspicious_rows,
            'clean_rows': clean,
            'is_locked': b.is_locked,
        })
    return Response(data)


@api_view(['GET'])
def get_records(request):
    org = get_user_org(request.user)
    records = EmissionRecord.objects.filter(batch__organization=org).order_by('-created_at') if org else EmissionRecord.objects.all().order_by('-created_at')

    source = request.GET.get('source')
    status_filter = request.GET.get('status')
    batch_id = request.GET.get('batch_id')
    scope_filter = request.GET.get('scope')

    if source:
        records = records.filter(source=source)
    if status_filter:
        records = records.filter(status=status_filter)
    if batch_id:
        records = records.filter(batch_id=batch_id)
    if scope_filter:
        records = records.filter(scope=scope_filter)

    page = int(request.GET.get('page', 1))
    page_size = 50
    start = (page - 1) * page_size
    end = start + page_size
    total = records.count()
    page_records = records[start:end]

    data = []
    for r in page_records:
        data.append({
            'id': r.id,
            'batch_id': r.batch_id,
            'source_row_number': r.source_row_number,
            'source': r.source,
            'scope': r.scope,
            'date': r.date,
            'description': r.description,
            'quantity': r.quantity,
            'unit': r.unit,
            'status': r.status,
            'validation_errors': r.validation_errors,
            'analysis_flags': r.analysis_flags,
            'transformations': r.transformations,
            'raw_data': r.raw_data,
            'approved_by': r.approved_by.username if r.approved_by else None,
            'approved_at': r.approved_at,
        })

    return Response({
        'total': total,
        'page': page,
        'page_size': page_size,
        'records': data,
    })


# ─── REVIEW ─────────────────────────────────────────────
@csrf_exempt
@api_view(['POST'])
def approve_record(request, record_id):
    current_user = request.user
    if not is_analyst(current_user):
        return Response({'error': 'Permission denied'}, status=403)

    org = get_user_org(request.user)
    try:
        record = EmissionRecord.objects.get(id=record_id)
        if org and record.batch.organization != org:
            return Response({'error': 'Permission denied'}, status=403)
    except EmissionRecord.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

    if record.batch.is_locked:
        return Response({'error': 'Batch is locked for audit. Cannot modify.'}, status=400)

    if record.status == 'approved':
        return Response({'error': 'Already approved'}, status=400)

    record.status = 'approved'
    record.approved_by = current_user if current_user.is_authenticated else None
    record.approved_at = datetime.now()
    record.save()

    return Response({'status': 'approved'})

@csrf_exempt
@api_view(['POST'])
def reject_record(request, record_id):
    current_user = request.user
    if not is_analyst(current_user):
        return Response({'error': 'Permission denied'}, status=403)

    org = get_user_org(request.user)
    try:
        record = EmissionRecord.objects.get(id=record_id)
        if org and record.batch.organization != org:
            return Response({'error': 'Permission denied'}, status=403)
    except EmissionRecord.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

    if record.batch.is_locked:
        return Response({'error': 'Batch is locked for audit. Cannot modify.'}, status=400)

    record.status = 'rejected'
    record.approved_by = current_user if current_user.is_authenticated else None
    record.approved_at = datetime.now()
    record.save()

    return Response({'status': 'rejected'})


@api_view(['POST'])
def lock_batch(request, batch_id):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can lock batches'}, status=403)

    org = get_user_org(request.user)
    try:
        batch = UploadBatch.objects.get(id=batch_id)
        if org and batch.organization != org:
            return Response({'error': 'Permission denied'}, status=403)
    except UploadBatch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=404)

    if batch.is_locked:
        return Response({'error': 'Batch already locked'}, status=400)

    pending_count = EmissionRecord.objects.filter(
        batch=batch,
        status='pending'
    ).count()

    if pending_count > 0:
        return Response({
            'error': f'{pending_count} rows still pending review. Review all rows before locking.'
        }, status=400)

    batch.is_locked = True
    batch.save()

    return Response({
        'message': f'Batch {batch.filename} locked for audit',
        'batch_id': batch_id,
    })


@api_view(['DELETE'])
def delete_batch(request, batch_id):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can delete batches'}, status=403)

    org = get_user_org(request.user)
    try:
        batch = UploadBatch.objects.get(id=batch_id)
        if org and batch.organization != org:
            return Response({'error': 'Permission denied'}, status=403)
    except UploadBatch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=404)

    if batch.is_locked:
        return Response({'error': 'Batch is locked for audit. Cannot delete.'}, status=400)

    batch.delete()
    return Response({'message': f'Batch {batch.filename} deleted'})


# ─── USER MANAGEMENT (admin only) ───────────────────────

@api_view(['POST'])
def create_user(request):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can create users'}, status=403)

    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role', 'analyst')  # 'admin' or 'analyst'

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)

    user = User.objects.create_user(username=username, password=password)
    group_name = 'Admin' if role == 'admin' else 'Analyst'
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    org_id = request.data.get('organization_id')
    if org_id:
        try:
            org = Organization.objects.get(id=org_id)
            UserProfile.objects.create(user=user, organization=org)
        except Organization.DoesNotExist:
            pass

    return Response({
        'message': f'User {username} created with role {group_name}',
        'username': username,
        'role': group_name,
    })


@api_view(['GET'])
def list_users(request):
    if not is_admin(request.user):
        return Response({'error': 'Only admins can view users'}, status=403)

    users = User.objects.all().prefetch_related('groups')
    data = []
    for u in users:
        groups = [g.name for g in u.groups.all()]
        data.append({
            'id': u.id,
            'username': u.username,
            'role': 'admin' if is_admin(u) else 'analyst',
            'groups': groups,
        })
    return Response(data)