import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsumerLayout from './ConsumerLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { orders } from '../../utils/api';
import { toast } from 'sonner';
import { ShoppingBag, CreditCard } from 'lucide-react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe('pk_test_51QntqsH7xN6aWpSEvUQGMWMJhp3Ua9gzmFZgJr4vD1XUcKTFzBnAGEbVGKWz2nSPvRQcCKEh0pGfOPPP1OxgJxvI00Edc9E3wv');

function CheckoutForm({ user, onLogout, cart, setCart }) {
  const stripe = useStripe();
  const elements = useElements();
  const navigate = useNavigate();

  const [deliveryMethod, setDeliveryMethod] = useState('pickup');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [pickupTime, setPickupTime] = useState('');
  const [charityRoundup, setCharityRoundup] = useState(false);
  const [loading, setLoading] = useState(false);

  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const tax = subtotal * 0.08; // Mock 8% tax
  const deliveryFee = deliveryMethod === 'delivery' ? 5.99 : 0;
  const netProceed = subtotal + tax + deliveryFee;
  const charityDac = netProceed * 0.0045;
  const charityDrlp = netProceed * 0.0045;
  const charityRoundupAmount = charityRoundup ? Math.ceil(netProceed + charityDac + charityDrlp) - (netProceed + charityDac + charityDrlp) : 0;
  const total = netProceed + charityDac + charityDrlp + charityRoundupAmount;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    if (deliveryMethod === 'delivery' && !deliveryAddress) {
      toast.error('Please enter delivery address');
      return;
    }

    if (deliveryMethod === 'pickup' && !pickupTime) {
      toast.error('Please select pickup time');
      return;
    }

    setLoading(true);

    try {
      // Create payment method
      const cardElement = elements.getElement(CardElement);
      const { error, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
      });

      if (error) {
        toast.error(error.message);
        setLoading(false);
        return;
      }

      // Create order
      const orderData = {
        items: cart,
        delivery_method: deliveryMethod,
        delivery_address: deliveryMethod === 'delivery' ? deliveryAddress : null,
        pickup_time: deliveryMethod === 'pickup' ? pickupTime : null,
        charity_roundup: charityRoundupAmount,
        payment_method_id: paymentMethod.id,
      };

      await orders.create(orderData);
      toast.success('Order placed successfully!');
      localStorage.removeItem('cart');
      setCart([]);
      navigate('/consumer/orders');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ConsumerLayout user={user} onLogout={onLogout}>
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Playfair Display, serif' }}>
            Checkout
          </h1>
          <p className="text-gray-600 mt-1">Complete your order</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Delivery Method */}
            <Card>
              <CardHeader>
                <CardTitle>Delivery Method</CardTitle>
              </CardHeader>
              <CardContent>
                <RadioGroup value={deliveryMethod} onValueChange={setDeliveryMethod}>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value="pickup" id="pickup" data-testid="pickup-option" />
                    <Label htmlFor="pickup" className="flex-1 cursor-pointer">
                      <div>
                        <p className="font-medium">Pickup</p>
                        <p className="text-sm text-gray-500">Free</p>
                      </div>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 border rounded-lg mt-2">
                    <RadioGroupItem value="delivery" id="delivery" data-testid="delivery-option" />
                    <Label htmlFor="delivery" className="flex-1 cursor-pointer">
                      <div>
                        <p className="font-medium">Delivery (DoorDash)</p>
                        <p className="text-sm text-gray-500">$5.99</p>
                      </div>
                    </Label>
                  </div>
                </RadioGroup>

                {deliveryMethod === 'delivery' && (
                  <div className="mt-4">
                    <Label htmlFor="address">Delivery Address</Label>
                    <Input
                      id="address"
                      data-testid="delivery-address"
                      placeholder="123 Main St, City, State ZIP"
                      value={deliveryAddress}
                      onChange={(e) => setDeliveryAddress(e.target.value)}
                      required
                    />
                  </div>
                )}

                {deliveryMethod === 'pickup' && (
                  <div className="mt-4">
                    <Label htmlFor="pickup-time">Pickup Time</Label>
                    <Input
                      id="pickup-time"
                      data-testid="pickup-time"
                      type="datetime-local"
                      value={pickupTime}
                      onChange={(e) => setPickupTime(e.target.value)}
                      required
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Payment */}
            <Card>
              <CardHeader>
                <CardTitle>Payment Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="border rounded-lg p-3 bg-gray-50">
                  <CardElement
                    options={{
                      style: {
                        base: {
                          fontSize: '16px',
                          color: '#424770',
                          '::placeholder': { color: '#aab7c4' },
                        },
                      },
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Test card: 4242 4242 4242 4242, any future date, any CVC
                </p>
              </CardContent>
            </Card>

            {/* Charity Roundup */}
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="pt-6">
                <div className="flex items-start space-x-3">
                  <Checkbox
                    id="roundup"
                    data-testid="charity-roundup"
                    checked={charityRoundup}
                    onCheckedChange={setCharityRoundup}
                  />
                  <Label htmlFor="roundup" className="cursor-pointer">
                    <p className="font-medium text-gray-900">Round up for charity</p>
                    <p className="text-sm text-gray-600">
                      Round up your total to ${Math.ceil(total - charityRoundupAmount).toFixed(2)} and donate{' '}
                      ${charityRoundupAmount.toFixed(2)} to your chosen charity
                    </p>
                  </Label>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Items */}
                <div className="space-y-2">
                  {cart.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-gray-600">
                        {item.name} x{item.quantity}
                      </span>
                      <span className="font-medium">${(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                <div className="border-t pt-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subtotal</span>
                    <span data-testid="subtotal">${subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tax (8%)</span>
                    <span data-testid="tax">${tax.toFixed(2)}</span>
                  </div>
                  {deliveryFee > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivery Fee</span>
                      <span data-testid="delivery-fee">${deliveryFee.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-emerald-600">
                    <span>Charity (DAC)</span>
                    <span data-testid="charity-dac">${charityDac.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-emerald-600">
                    <span>Charity (DRLP)</span>
                    <span data-testid="charity-drlp">${charityDrlp.toFixed(2)}</span>
                  </div>
                  {charityRoundup && (
                    <div className="flex justify-between text-emerald-600">
                      <span>Charity Round-up</span>
                      <span data-testid="charity-roundup-amount">${charityRoundupAmount.toFixed(2)}</span>
                    </div>
                  )}
                </div>

                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span data-testid="total">${total.toFixed(2)}</span>
                  </div>
                </div>

                <Button
                  data-testid="place-order-btn"
                  onClick={handleSubmit}
                  disabled={!stripe || loading}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? 'Processing...' : 'Place Order'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ConsumerLayout>
  );
}

export default function ConsumerCheckout({ user, onLogout }) {
  const [cart, setCart] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    } else {
      navigate('/consumer/browse');
    }
  }, [navigate]);

  if (cart.length === 0) {
    return (
      <ConsumerLayout user={user} onLogout={onLogout}>
        <Card>
          <CardContent className="py-12 text-center">
            <ShoppingBag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Your cart is empty</p>
            <Button onClick={() => navigate('/consumer/browse')} className="mt-4">
              Browse Deals
            </Button>
          </CardContent>
        </Card>
      </ConsumerLayout>
    );
  }

  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm user={user} onLogout={onLogout} cart={cart} setCart={setCart} />
    </Elements>
  );
}
