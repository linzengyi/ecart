from django.db import models

# Create your models here.
class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    store_code = models.CharField(max_length=10, unique=True)
    store_name = models.CharField(max_length=255)
    store_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Device(models.Model):
    device_id = models.AutoField(primary_key=True)
    device_code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class StoreDevice(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    member_name = models.CharField(max_length=255, null=True, blank=True)
    account = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MemberDevice(models.Model):
    # 定義 Member 和 Device 的主鍵欄位
    member_id = models.ForeignKey('Member', on_delete=models.CASCADE)  # 參照 Member 模型的主鍵
    device_id = models.ForeignKey('Device', on_delete=models.CASCADE)  # 參照 Device 模型的主鍵
    
    # 狀態欄位，允許為 null 或空值
    status = models.CharField(max_length=10, null=True, blank=True)
    
    # 建立日期和修改日期欄位
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 設置索引
    class Meta:
        # 定義索引：將 member_id 和 device_id 設為一般索引
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['device_id']),
        ]


class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    member = models.ForeignKey(Member, on_delete=models.DO_NOTHING)
    product_code = models.CharField(max_length=10, blank=True, null=True)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    status = models.CharField(max_length=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_code = models.CharField(max_length=10)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_no = models.CharField(max_length=12, unique=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    total_amount = models.IntegerField()
    payment_method = models.CharField(max_length=20, choices=[('money', 'Money'), ('credit_card', 'Credit Card')])
    status = models.CharField(max_length=1, choices=[('F', 'Paid')], null=True, blank=True)  # NULL = Pending
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderItem(models.Model):
    orderitem_id = models.AutoField(primary_key=True)
    order_no = models.ForeignKey(to="Order",to_field="order_no", on_delete=models.CASCADE)
    product_code = models.CharField(max_length=10)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    quantity = models.PositiveIntegerField()
    subtotal = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity  # 計算小計
        super().save(*args, **kwargs)