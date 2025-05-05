from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.forms.models import model_to_dict
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from myapp.models import Store, Device, StoreDevice, Product, Member, CartItem, MemberDevice, Order, OrderItem
from myapp.lib.utils import generate_order_number
# Create your views here.


# api_url = "http://192.168.0.166:8080/"
# api_url = "http://192.168.58.22:8080/"
api_url = "https://ecart-mpqg.onrender.com/"

def test(request):
    return HttpResponse("test")


def index(request):
    storeCode = request.GET['store']
    deviceCode = request.GET['device']

    return redirect(f'/login/?store={storeCode}&device={deviceCode}')


@csrf_exempt
def register(request):
    storeCode = request.GET['store']
    deviceCode = request.GET['device']
    
    if request.method == "POST":
        isError = False
        errorMessage = ""
        try:
            account = request.POST["userAccount"]
            password = request.POST["userPassword"]
            checkPassword = request.POST["userCheckPassword"]

            if (checkPassword == password):
                # print("密碼檢核正確")
                Member.objects.create(
                    account = account,
                    password_hash = make_password(password),
                    status = 'active'
                )

                return redirect(f'/login/?store={storeCode}&device={deviceCode}')
            else:
                isError = True
                errorMessage = "密碼與確認密碼不同!"
        except:
            isError = True
            errorMessage = "無法註冊!"
    
    # print("進入註冊頁")
    return render(request, 'register.html', locals())


@csrf_exempt
def login(request):
    isError = False
    errorMessage = ""

    storeCode = request.GET["store"]
    deviceCode = request.GET["device"]

    # print("store code:"+ storeCode)
    # print("device code:"+ deviceCode)
    
    if request.method == "POST":
        try:
            account = request.POST["userAccount"]
            password = request.POST["userPassword"]

            # print("account: "+account)
            # print("password: "+password)

            memberData = Member.objects.get(account = account)
            storeData = Store.objects.get(store_code = storeCode)
            deviceData = Device.objects.get(device_code = deviceCode)
            # print(memberData)
            # print(type(memberData))

            # print(storeData)
            # print(type(storeData))

            # print(deviceData)
            # print(type(deviceData))

            if (memberData != None and check_password(password, memberData.password_hash)):
                request.session["member"] = { 
                    "id":memberData.member_id, 
                    "name": memberData.member_name or "",
                    "account": memberData.account
                }
                request.session["storeData"] = {
                    "id": storeData.store_id,
                    "code": storeData.store_code,
                    "name": storeData.store_name,
                }
                request.session["deviceData"] = {
                    "id": deviceData.device_id,
                    "code": deviceData.device_code
                }
            else:
                isError = True
                errorMessage = "帳號或密碼有誤"
        except:
            isError = True
            errorMessage = "登入失敗"
        finally:
            print("finally")
            # 使用 create() 方法新增資料
            member_device = MemberDevice.objects.create(
                member_id=memberData,  # 參照 Member 實例
                device_id=deviceData,  # 參照 Device 實例
                status='active'   # 設定狀態
            )

            return redirect("/member/")

    return render(request, 'login.html', locals())


def logout(request):
    if (request.session["member"] != None):
        storeCode = request.session["storeData"]["code"]
        deviceCode = request.session["deviceData"]["code"]
        memberAccount = request.session["member"]["account"]
        
        del request.session["member"]

        memberData = Member.objects.get(account = memberAccount)
        deviceData = Device.objects.get(device_code = deviceCode)
        member_device = MemberDevice.objects.get(
                    member_id = memberData,  # 參照 Member 實例
                    device_id = deviceData,  # 參照 Device 實例
                    status='active'          # 設定狀態
        )

        # print(f"storeCode = {storeCode}")
        # print(f"deviceCode = {deviceCode}")
        # print(f"memberAccount = {memberAccount}")
        # print(model_to_dict(member_device))

        if (member_device is not None):
            member_device.status = "inactive"
            member_device.save()

    # return HttpResponse("test")
    return redirect(f'/login/?store={storeCode}&device={deviceCode}')
    
@csrf_exempt
def forgetpassword(request):
    storeCode = request.GET['store']
    deviceCode = request.GET['device']
    
    if (request.method == "POST"):
        isError = False
        errorMessage = ""

        account = request.POST["userAccount"]
        newPassword = request.POST["newUserPassword"]
        checkNewPassword = request.POST["userCheckNewPassword"]

        try:
            memberData = Member.objects.get(account = account)
            print(memberData)
            
            if (newPassword != checkNewPassword):
                isError = True
                errorMessage = "新密碼與確認密碼不同!"
            else:
                try:
                    memberData.password_hash = make_password(newPassword)
                    memberData.save()

                    return redirect(f'/login/?store={storeCode}&device={deviceCode}')
                except:
                    isError = True
                    errorMessage = "密碼更新失敗"
        except:
            isError = True
            errorMessage = "帳號不存在"

    return render(request, 'forgetpassword.html', locals())

@csrf_exempt
def member(request):
    memberData = request.session.get("member", None)

    if (memberData == None):
       return redirect('/login/?store=0&device=0')
    elif(request.method == "POST"):
        isError = False
        errorMessage = ""
        try:
            memberId = request.POST['memberId']
            name = request.POST['memberName']
            password = request.POST['memberPassword']

            # print(memberId, name, password)
            memberObj= Member.objects.get(member_id=memberId)
            
            memberObj.member_name = name
            if (password != ""):
                memberObj.password_hash = make_password(password)

            memberObj.save()
            
            request.session["member"]["name"] = name
            # print(request.session["member"])
        except:
            isError = True
            errorMessage = "更新失敗"
    # print("out: ", memberData)

    return render(request, 'member.html', locals())

@csrf_exempt
def cart(request, step=1):
    API_URL = api_url

    storeData = request.session['storeData']
    deviceData = request.session['deviceData']
    memberData = request.session["member"]
    
    # print(storeData)
    # print(deviceData)

    ecart_lists = CartItem.objects.filter(store=storeData["id"], 
                                    device = deviceData["id"],
                                    member = memberData["id"]).exclude(status__in=['D', 'F']).order_by('created_at')
    
    shopName = storeData["name"]
    count = len(ecart_lists)
    subTotal = 0

    for item in ecart_lists:
        product = model_to_dict(item)
        # print(model_to_dict(item))
        subTotal += product['price']

    template = 'cart.html'
    if (step == 2):
        template = 'cart_paymethod.html'
    elif(step == 3):
        # print("付款方式:")
        # print(request.POST['paymentMethod'])

        paymentMethod = request.POST['paymentMethod']
        # credit_card
        try:
            # 產生訂單號碼
            count = Order.objects.filter(status='F').count()
            orderNo = generate_order_number(count+1)
            print(f"訂單號碼:{orderNo}")
            cart_items = CartItem.objects.filter(
                    member=memberData["id"],
                    device=deviceData["id"]
                ).filter(
                    Q(status='d') | Q(status__isnull=True)
                ).values(
                    'product_code', 'product_name', 'price'
                ).annotate(
                    quantity=Count('product_name')
                )
            
            memberObj = Member.objects.get(member_id = memberData["id"])
            storeObj = Store.objects.get(store_id = storeData["id"])

            orderObj = Order.objects.create(
                order_no = orderNo,
                member = memberObj,
                store = storeObj,
                total_amount = subTotal,
                payment_method = paymentMethod,
                status = 'F'
            )

            buyItems = []
            for item in cart_items:
                orderItem = OrderItem(order_no = orderObj,
                    product_code = item['product_code'],
                    product_name = item['product_name'],
                    price = item['price'],
                    quantity = item['quantity'])
                orderItem.save()
                buyItems.append(orderItem)

            # 取得當前日期（年月日）
            now = timezone.now()
            start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

            # 取得當前時間
            end_of_day = now

            CartItem.objects.filter(
                member=memberData["id"],
                device=deviceData["id"],
                store=storeData["id"],
                created_at__range=(start_of_day, end_of_day),
            ).filter(
                Q(status__isnull=True) | Q(status='')
            ).update(status='F')
     
            template = 'cart_final.html'
        except Exception as e:
           print(e)
        
    return render(request, template, locals())


def orders(request):
    memberSessionData = request.session.get("member", None)
    if (memberSessionData == None):
        return redirect('/login/?store=none&device=none')
    # print("====== member session data =====")
    # print(memberSessionData)

    try:
        orderList = Order.objects.filter(member_id = memberSessionData["id"]).order_by('-order_no').values()
        # print("===== order list =====")
        # print(orderList)
    
    except Exception as e:
        print(e)

    return render(request, 'orders.html', locals())

def orderDetail(request, orderNo):
    memberSessionData = request.session.get("member", None)
    if (memberSessionData == None):
        return redirect('/login/?store=none&device=none')

    # print(f"==== order detail page =====")
    # print(f"order no = {orderNo}")
    
    try:
        orderData = Order.objects.select_related('store').filter(order_no=orderNo).values(
        'order_no', 'payment_method', 'total_amount', 'store__store_name', 'created_at')
        # print(" ===== 訂單資訊 =====")
        # print(orderData)

        orderList = OrderItem.objects.filter(order_no_id=orderNo).values()
        # print(" ===== 訂單明細 =====")
        # print(orderList)
        return render(request, 'order_detail.html', locals())
    except Exception as e:
        print(e)
        return HttpResponse("訂單不存在")

#########################################################################
#api
@csrf_exempt
@require_http_methods(["POST"])
def addecartItem(request):
    try:
        product_code = request.POST['product_code']
        store_code = request.POST['store_code']         # 預設，從裝置提供
        device_code = request.POST['device_code']       # 預設，從裝置提供
        # print(f"product_code:{product_code}, store_code:{store_code}, device_code:{device_code}")
        # print("=================================")
        
        try:
            productData = Product.objects.get(product_code = product_code)
            # print(model_to_dict(productData))

            storeData = Store.objects.get(store_code = store_code)
            # print(model_to_dict(storeData))
            deviceData = Device.objects.get(device_code = device_code)
            # print(model_to_dict(deviceData))
            
            memberDeviceData = model_to_dict(MemberDevice.objects.get(device_id=deviceData.device_id, status='active'))
            # print(memberDeviceData)

            memberData = Member.objects.get(member_id=memberDeviceData['member_id'])
            # print(model_to_dict(memberData))

            cartItem = CartItem(
                store = storeData,
                device = deviceData,
                member = memberData,
                product_code = productData.product_code,
                product_name = productData.product_name,
                price = productData.price
            )
        
            cartItem.save()

            return JsonResponse({ 'success': True, 'message': '' })
        except Exception as e:
            print("錯誤訊息:")
            print(e)
            return JsonResponse({ 'success': True, 'message': '無法新增，傳入資料查詢不存在!'})
    except:
        return JsonResponse({ 'success': False, 'message': '無法新增，缺必要參數!'})


@csrf_exempt
def delecartItem(request):
    # 收到商品碼查詢最新一筆紀錄更新狀態小d(刪除待確認)，狀態為小d則更新狀態大D(刪除)
    if (request.method == "POST"):
        try: 
            product_code = request.POST['product_code']
            store_code = request.POST['store_code']         # 預設，從裝置提供
            device_code = request.POST['device_code']       # 預設，從裝置提供

            productData = Product.objects.get(product_code = product_code)
            # print(model_to_dict(productData))

            storeData = Store.objects.get(store_code = store_code)
            # print(model_to_dict(storeData))
            deviceData = Device.objects.get(device_code = device_code)
            # print(model_to_dict(deviceData))
            
            memberDeviceData = model_to_dict(MemberDevice.objects.get(device_id=deviceData.device_id, status='active'))
            # print(memberDeviceData)

            memberData = Member.objects.get(member_id=memberDeviceData['member_id'])
            # print(model_to_dict(memberData))

            # 取得商品
            productItemList = CartItem.objects.filter(store = storeData,
                                device = deviceData,
                                member = memberData,
                                product_name = productData.product_name
                            ).filter(Q(status='d') | Q(status__isnull=True)).order_by('-created_at')

            productItem = None
            first = True
            for product in productItemList:
                if (first and productItem == None):
                    productItem = product
                    first = False
                elif (product.status == 'd'):
                    productItem = product

            # print(type(productItem))
            # print(productItem)
            # print(model_to_dict(productItem))

            message = ''
            success = False
            if (productItem != None):
                if (productItem.status == None):
                    productItem.status = 'd' # 更新status = 'd' 
                    productItem.save()
                elif (productItem.status == 'd'):
                    productItem.status = 'D' # 更新status = 'D' 
                    productItem.save()

                success = True
            else:
                message = '商品未加入購物車'
            
            return JsonResponse({ 'success': success, 'message': message })
        except Exception as e:
            print("錯誤訊息:")
            print(e)
            return JsonResponse({ 'success': False, 'message': '無法刪除，缺必要參數!'})
    else:
        return HttpResponseNotAllowed(['GET','DELETE', 'PUT'])



def init(request):
    # 使用 ORM 建立新店鋪
    # new_store = Store.objects.create(
    #     store_code='ST001',
    #     store_name='方便購-幼獅店',
    #     store_address='桃園市幼獅路3段',
    # )
    # 使用 ORM 建立新裝置
    # new_device = Device.objects.create(
    #     device_code= 'a00001',
    #     status='active'
    # )
    
    # new_store = Store.objects.get(store_id=1)
    # new_device = Device.objects.get(device_id=1)
    # StoreDevice.objects.create(
    #     store = new_store,
    #     device = new_device
    # )

    # 使用 ORM 建立 10 筆商品資料
    # products = [
    #     Product(product_code="P00001", product_name="可口可樂 125ml", price=105, status="active"),
    #     Product(product_code="P00002", product_name="黑松沙士 125ml", price=90, status="active"),
    #     Product(product_code="P00003", product_name="舒潔衛生紙500抽 6包", price=120, status="active"),
    #     Product(product_code="P00004", product_name="味味A排骨雞麵 6包", price=80, status="active"),
    #     Product(product_code="P00005", product_name="維力炸醬麵 6包", price=90, status="active"),
    #     Product(product_code="P00006", product_name="滿漢大餐", price=90, status="active"),
    #     Product(product_code="P00007", product_name="統一AB優酪乳 250ml", price=150, status="active"),
    #     Product(product_code="P00008", product_name="多力多滋", price=60, status="active"),
    #     Product(product_code="P00009", product_name="OREO", price=60, status="active"),
    #     Product(product_code="P00010", product_name="可樂果", price=50, status="active")
    # ]

    # 批次保存商品資料
    # Product.objects.bulk_create(products)

    # account="0912123456"
    # deviceCode="a00001"
    # memberData = Member.objects.get(account = account)
    # deviceData = Device.objects.get(device_code = deviceCode)

    # member_device = MemberDevice.objects.create(
    #             member_id=memberData,  # 參照 Member 實例
    #             device_id=deviceData,  # 參照 Device 實例
    #             status='active'   # 設定狀態
    #         )
    
    # print(member_device)
    # print(type(member_device))
    count = Order.objects.filter(status='F').count()
    print(type(count), count)
    print(generate_order_number(count))
    return HttpResponse("ok")

'''
products = [{'no':'A01' ,'name': '可口可樂 125ml', 'price': 60 },
         {'no':'A02' ,'name': '舒潔衛生紙500抽 6包', 'price': 70 },
         {'no':'A03' ,'name': '味味A排骨雞麵 6包', 'price': 80 },
         {'no':'A04' ,'name': '統一AB優酪乳 250ml', 'price': 130 },
         {'no':'A05' ,'name': '維力炸醬麵 6包', 'price': 120 }]


'''

